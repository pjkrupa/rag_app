import requests, time
from app.core.config import Configurations
from app.core.errors import handle_api_errors
from app.models import ChromaDbResult

class EmbeddingsClient:
    def __init__(self, configs: Configurations):
        self.configs = configs
        self.logger = configs.logger

    @handle_api_errors(default=[])
    def embed(self, text: str) -> list[float]:
        """
        Hits embeddings API to return vector embeddings 
        """
        start = time.time()

        url = f"{self.configs.embeddings_url}/embeddings"

        resp = requests.post(
            url,
            json={"text": text},
            timeout=20
        )
        resp.raise_for_status()

        data = resp.json()
        self.logger.debug(self.logger.debug(
            "Request: %s %s | headers=%s | body=%s",
            resp.request.method,
            resp.request.url,
            dict(resp.request.headers),
            resp.request.body,
            )
        )
        self.logger.debug(
            "POST %s | status=%s | headers=%s | body=%s",
            url,
            resp.status_code,
            resp.headers.get("Content-Type"),
            resp.text[:500]
            )
        
        embedding = data.get("embedding", [])

        self.logger.info("Successfully fetched embedding.")
        self.logger.info(f"RESPONSE TIME: {time.time() - start:.3f}s")
        self.logger.info(f"EMBED FETCH STATUS: {resp.status_code}")
        self.logger.debug(f"Embedding returned by embeddings.embed: {embedding}")
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

        logger.info("Successfully reranked.")
        logger.info(f"RESPONSE TIME: {time.time() - start:.3f}s")
        logger.info(f"RERANK STATUS: {resp.status_code}")

        return resp.json()