import os, time, json
import requests
from datetime import datetime
import chromadb
from logging import Logger
from functools import wraps
from models import ChromaDbResult, Message, Parameters, Configurations, Tool
from tools import TOOLS
from litellm import completion
from pprint import pprint

# a quick wrapper that handles errors and logs them.
def handle_api_errors(default):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = kwargs.get("logger")
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if logger:
                    logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                else:
                    raise e
            return default
        return wrapper
    return decorator

class Chat:
    def __init__(self, configs: Configurations, id: str = ""):
        self.configs = configs
        self.id = id
        self.messages = [Message(role="system", content=configs.system_prompt)]
    
    def add_message(self, message: Message):
        self.messages.append(message)

class EmbeddingsClient:
    def __init__(self, configs: Configurations):
        self.configs = configs
    
    @handle_api_errors(default=[])
    def embed(self, text: str) -> list[float]:
        """
        Hits a custom API that uses a transformer to calculate embeddings.

        Parameters:
        text -> The text to be converted to embeddings, str.
        config -> Configurations object

        Returns:
        The embedding, list[float]
        """
        logger = self.configs.logger
        start = time.time()

        resp = requests.post(
            f"{self.configs.embeddings_url}/embeddings",
            json={"text": text},
            timeout=20
        )
        resp.raise_for_status()

        data = resp.json()
        embedding = data.get("embedding", [])

        logger.info("-" * 50)
        logger.info("Successfully fetched embedding.")
        logger.info(f"RESPONSE TIME: {time.time() - start:.3f}s")
        logger.info(f"EMBED FETCH STATUS: {resp.status_code}")
        logger.info("-" * 50)

        return embedding

    @handle_api_errors(default={})
    def rerank(
        self,
        query_text: str, 
        results: list[ChromaDbResult],
        ) -> dict:
        """
        Runs reranking on the ChromaDB results and returns the IDs of the top_n query responses.

        Parameters:
        query_text -> the text of the original query, str
        results -> a list of results in the form of ChromaDbResult model objects, list[ChromaDbResult]
        url -> URL of the embedding server, str
        logger -> Logger object, Logger

        Returns:
        dict{
            "results": [
                {"id": str, "score": float},
                {"id": str, "score": float}
            ]
            }
        """
        logger = self.configs.logger
        endpoint = f"{self.configs.embeddings_url}/reranking"
        start = time.time()
        items = [
            {"id": result.id, "text": result.document} for result in results
        ]

        request_payload = {
            "query": query_text, 
            "items": items, 
            "top_n": self.configs.rerank_top_n
            }
        
        resp = requests.post(
            endpoint, 
            json=request_payload, 
            timeout=20
        )

        logger.info("-" * 50)
        logger.info("Successfully reranked.")
        logger.info(f"RESPONSE TIME: {time.time() - start:.3f}s")
        logger.info(f"RERANK STATUS: {resp.status_code}")
        logger.info("-" * 50)
        return resp.json()

class LiteLlmClient:
    def __init__(
            self, 
            configs: Configurations, 
            tools: list[Tool]):
        self.configs = configs
        self.tools = tools

    # need to add error handling and retries for this.
    def request(self, messages: list[Message]
        ) -> Message:
        params = Parameters(
                model=self.configs.model, 
                messages=messages, 
                api_base=self.configs.ollama_api_base, 
                tools=self.tools
                )
        return completion(**params.model_dump())
    
    def get_messsage(self, response):
        lite_msg = response.choices[0].message
        return Message.model_validate(lite_msg.model_dump())

#FINISH THIS. 
class RagClient:
    def __init__(self, configs: Configurations):
        self.configs = configs
        self.emb_client = EmbeddingsClient(configs=configs)
# ------------------------------

@handle_api_errors(default={})
def query_collection(
        query_embedding: list[float],
        collection: str,
        config: Configurations
        ) -> list[ChromaDbResult]:
    """
    Queries a collection in a ChromaDB server.

    Parameters:
    query_embedding -> Embedding used to query ChromaDB, get it by calling embed() with the query str, list[float]
    collection -> name of the collection to be queried, str
    config -> the Configuration object with all the configs

    Returns:
    list of ChromaDbResult objects
    """

    chroma_client = chromadb.HttpClient(
        host=config.chromadb_host, 
        port=config.chromadb_port
        )
    col = chroma_client.get_collection(name=collection)
    raw = col.query(query_embeddings=[query_embedding], n_results=config.chroma_top_n)
    return format_query_result(raw)
    

def format_query_result(raw: dict) -> list[ChromaDbResult]:
    """
    Takes the raw results from a ChromaDB query and turns them into a list of ChromaDdResult objects.

    Parameters:
    raw -> The output of query_collection(), a dictionary from a ChromaDB query

    Returns:
    A list of ChromaDbResult objects
    """
    
    results = [ChromaDbResult(
        id=raw["ids"][0][i],
        document=raw["documents"][0][i], 
        metadata=raw["metadatas"][0][i],
        distance=raw["distances"][0][i]
        ) for i in range(len(raw))]
    return results
    
def filter_results(
        results: list[ChromaDbResult], 
        reranked: list[dict],
        ) -> list[ChromaDbResult]:
    filtered_results = []
    print(f"reranked type: {type(reranked)}")
    for item in reranked:
        for result in results:
            if result.id == item["id"]:
                filtered_results.append(result)
    return filtered_results
    
def handle_tool_call(
        response_message: Message,
        config: Configurations,
        ) -> Message:
    """
    should return a Message object with "role" set to "tool"
    """
    tool_names = [item["name"] for item in TOOLS]
    logger = config.logger

    for tool_call in response_message.tool_calls:

        if tool_call.function.name not in tool_names:
            logger.error(f"The model tried to call tool {tool_call.function.name}, which is not in the list of tool names: {tool_names} ")
            return Message(role='tool', tool_call_id=tool_call.id, content='There is no tool with that name')
        elif tool_call.function.name == "gdpr_query":
            print("pretty-printing the whole tool call... ")
            pprint(tool_call)
            arguments = json.loads(tool_call.function.arguments)
            print(f"arguments type is: {type(arguments)}")
            print(arguments)

            # gets the vector representation of the query
            emb_client = EmbeddingsClient(configs=config)
            vec_query = emb_client.embed(text=arguments["query_text"])

            # returns list of ChromaDbResult objects
            chromadb_response = query_collection(
                query_embedding=vec_query, 
                collection="gdpr", 
                config=config
                )
            
            # runs the reranking
            rerank_result = emb_client.rerank(
                query_text=arguments["query_text"], 
                results=chromadb_response,
                )
            
            # pprint(rerank_result)
            #applies the reranking findings
            final_results = filter_results(results=chromadb_response, reranked=rerank_result["results"])
            json_str = json.dumps([obj.model_dump() for obj in final_results])
            return Message(role='tool', tool_call_id=tool_call.id, content=json_str)
            
            

            


