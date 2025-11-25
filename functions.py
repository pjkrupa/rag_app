import os, time, json
import requests
from datetime import datetime
import chromadb
from logging import Logger
from functools import wraps
from models import ChromaDbResult, Message, Parameters, Configurations, Tool
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
        Hits embeddings API to return vector embeddings 
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

        return embedding

    def _build_rerank_payload(self, query_text: str, results: list[ChromaDbResult]) -> dict:
        items = [ {"id": r.id, "text": r.document} for r in results ]
        return {
            "query": query_text,
            "items": items,
            "top_n": self.configs.rerank_top_n
        }
    
    @handle_api_errors(default={})
    def rerank(
        self,
        query_text: str, 
        results: list[ChromaDbResult],
        ) -> dict:
        """
        Hits an embedding API to run reranking on the ChromaDB results and return the IDs of the top_n query responses.

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
        request_payload = self._build_rerank_payload(query_text, results)
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

class LlmClient:
    def __init__(
            self, 
            configs: Configurations, 
            tools: list[Tool]):
        self.configs = configs
        self.tools = tools

    # TODO: need to add error handling and retries for this.
    # TODO: also need to add an optional tools parameter for if user wants to call tools
    def send_request(self, messages: list[Message]
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


class ToolHandler:

    def __init__(self, configs: Configurations, tools: list[Tool]):
        self.configs = configs
        self.tools = tools
        self.tool_names = [tool.function.name for tool in tools]
        self.logger = configs.logger
        self.rag = RagClient(configs, tools)

    def handle(self, message: Message):
        for tool_call in message.tool_calls:

            if tool_call.function.name not in self.tool_names:
                self.logger.error(f"The model tried to call tool {tool_call.function.name}, which is not in the list of tool names: {self.tool_names} ")
                return Message(role='tool', tool_call_id=tool_call.id, content='There is no tool with that name.')
            
            # need an elif block for each name in tool_names
            elif tool_call.function.name == "gdpr_query":
                arguments = json.loads(tool_call.function.arguments)
                self.logger.info(f"Call for tool {tool_call.function.name}: {arguments}")
                return self.rag.generate( 
                    query=arguments["query_text"], 
                    tool_call_id=message.tool_call_id, 
                    collection="gdpr")
            
            # logs an error if a tool exists but handling hasn't been added yet
            else:
                self.logger.error(f"Tool call for {tool_call.function.name} not handled. Have you added handling for it yet??")
                return Message(role='tool', tool_call_id=tool_call.id, content='Tool not found.')


class RagClient:

    def __init__(self, configs: Configurations, tools: list[Tool]):
        self.configs = configs
        self.emb_client = EmbeddingsClient(configs=configs)

    def generate(self, query: str, collection: str, tool_call_id: str) -> Message:
        vec_query = self.emb_client.embed(text=query)
        chroma_docs = self._get_docs(query_embedding=vec_query, collection=collection)
        reranked = self.emb_client.rerank(query_text=query, results=chroma_docs)
        final_results = self._filter_results(results=chroma_docs, reranked=reranked["results"])
        json_str = json.dumps([obj.model_dump() for obj in final_results])
        return Message(role='tool', tool_call_id=tool_call_id, content=json_str)
    
    @handle_api_errors(default={})
    def _get_docs(self,
        query_embedding: list[float], 
        collection: str, 
        ) -> list[ChromaDbResult]:
        chroma_client = chromadb.HttpClient(
        host=self.configs.chromadb_host, 
        port=self.configs.chromadb_port
        )
        col = chroma_client.get_collection(name=collection)
        raw = col.query(query_embeddings=[query_embedding], n_results=self.configs.chroma_top_n)
        return self._format_query_result(raw)

    def _format_query_result(self, raw: dict) -> list[ChromaDbResult]:
        results = [ChromaDbResult(
            id=raw["ids"][0][i],
            document=raw["documents"][0][i], 
            metadata=raw["metadatas"][0][i],
            distance=raw["distances"][0][i]
            ) for i in range(len(raw))]
        return results

    def _filter_results(
            self,
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
            
            
            

            


