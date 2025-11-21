import os, time
import requests
from datetime import datetime
import chromadb
from logging import Logger
from functools import wraps
from models import ChromaDbResult
from tools import TOOLS

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

 
@handle_api_errors(default=[])
def embed(
    text: str, 
    url: str, 
    logger: Logger
    ) -> list[float]:
    """
    Hits a custom API that uses a transformer to calculate embeddings.

    Parameters:
    text -> The text to be converted to embeddings, str.
    url -> The base URL for the API, string
    logger -> Logger object, Logger

    Returns:
    The embedding, list[float]
    """
    start = time.time()

    resp = requests.post(
        f"{url}/embeddings",
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

# Gotta refactor this to take list[ChromaDbResult] as its input
@handle_api_errors(default={})
def rerank(
        query_text: str, 
        results: list[ChromaDbResult],
        url: str,
        top_n: int,
        logger: Logger
        ) -> dict:
    """
    Runs reranking and gets the IDs of the top_n query responses.

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
    endpoint = f"{url}/reranking"
    start = time.time()
    items = [
        {"id": result.id, "text": result.document} for result in results
    ]

    request_payload = {"query": query_text, "items": items, "top_n": top_n}
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


@handle_api_errors(default={})
def query_collection(
        query_embedding: list[float],
        collection: str,
        chroma_host: str,
        chroma_port: int,
        n_results: int
        ) -> dict:
    """
    Queries a collection in a ChromaDB server.

    Parameters:
    query_embedding -> Embedding used to query ChromaDB, get it by calling embed() with the query str, list[float]
    collection -> name of the collection to be queried, str
    chroma_host -> hostname of the ChromaDB server, should be defined in the .env file, str
    chroma_port -> port used by ChromaDB, should be defined in the .env file, int
    n_results -> number of results to return, int

    Returns:
    Raw ChromaDB response, a dict, something like:
    {   'data': None,
        'distances': [[int, int]],
        'documents': [[str, str]],
        'embeddings': None,
        'ids': [[str, str]],
        'included': ['metadatas', 'documents', 'distances'],
        'metadatas': [[dict, dict]],
        'uris': None}
    """

    chroma_client = chromadb.HttpClient(
        host=chroma_host, 
        port=chroma_port
        )
    col = chroma_client.get_collection(name=collection)
    return col.query(query_embeddings=[query_embedding], n_results=n_results)
    

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
        metadatas=raw["metadata"][0][i],
        distance=raw["distances"][0][i]
        ) for i in len(raw)]
    return results
    
    


    

    reranked = rerank(query_text=query_text, results=results)
    final = [
        {
            "id": item["id"],
            "score": item["score"],
            "document": results[item["id"]]["document"],
            "metadata": results[item["id"]]["metadata"],
            "distance": results[item["id"]]["distance"],
        }
        for item in reranked["results"]
    ]
    print(f"response type: {type(final)}")
    return final