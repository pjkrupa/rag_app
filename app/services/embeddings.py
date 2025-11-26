import requests, time
from app.core.config import Configurations
from app.core.errors import handle_api_errors
from app.models import ChromaDbResult

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