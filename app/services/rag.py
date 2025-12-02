import json
import chromadb
from app.core.config import Configurations
from app.core.errors import handle_api_errors, RagClientFailedError
from app.models import ChromaDbResult, Tool, Message
from app.services.embeddings import EmbeddingsClient

class RagClient:

    def __init__(self, configs: Configurations):
        self.configs = configs
        self.emb_client = EmbeddingsClient(configs=configs)
        self.logger = configs.logger

    def generate(self, query: str, collection: str, tool_call_id: str) -> tuple[Message, list[ChromaDbResult]]:
        try:
            vec_query = self.emb_client.embed(text=query)
            chroma_docs = self._get_docs(query_embedding=vec_query, collection=collection)
            reranked = self.emb_client.rerank(query_text=query, results=chroma_docs)
            documents = self._filter_results(results=chroma_docs, reranked=reranked["results"])
            json_str = json.dumps([obj.model_dump() for obj in documents])
            return Message(role='tool', tool_call_id=tool_call_id, content=json_str), documents
        except Exception as e:
            self.logger.error(f"Something went wrong with the RAG: {e}")
            raise RagClientFailedError("The RAG client failed") from e
    
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