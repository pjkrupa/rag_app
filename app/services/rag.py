import json
import chromadb
from app.core.config import Configurations
from app.core.errors import RagClientFailedError, MetadataFilterError
from app.models import ChromaDbResult, Message, MessageDocuments, RerankResponse
from app.services.embeddings import EmbeddingsClient

class RagClient:

    def __init__(self, configs: Configurations):
        self.configs = configs
        self.emb_client = EmbeddingsClient(configs=configs)
        self.logger = configs.logger

    def chroma_query(
            self, 
            arguments: dict, 
            collection: str, 
            tool_call_id: str
        ) -> MessageDocuments:
        
        query = arguments.get("query_text", "")

        try:
            vec_query = self.emb_client.embed(text=query)
            if not vec_query:
                raise ValueError("Empty embedding")
            chroma_docs = self._query(query_embedding=vec_query, collection=collection)
            reranked = self.emb_client.rerank(query_text=query, results=chroma_docs)
            documents = self._filter_results(results=chroma_docs, reranked=reranked)
            json_str = json.dumps([obj.model_dump() for obj in documents])
            return MessageDocuments(
                message=Message(
                    role='tool', 
                    tool_call_id=tool_call_id, 
                    content=json_str
                    ), 
                documents=documents
                )
        except Exception as e:
            self.logger.error(f"Something went wrong with the RAG process: {e}")
            raise RagClientFailedError("The RAG client failed while sending a query for vector embeddings") from e

    def chroma_get(
            self,
            arguments: dict,
            collection: str,
            tool_call_id: str
        ) -> MessageDocuments:
        try:
            metadata_filter = self._validate_filter(arguments)
        except (ValueError, TypeError) as e:
            self.logger.error(f"Problem with the metadata filter: {e}")
            raise MetadataFilterError(f"The metadata filter is invalid") from e

        try:
            documents = self._get(collection=collection, metadata_filter=metadata_filter)
            json_str = json.dumps([obj.model_dump() for obj in documents])
            return MessageDocuments(message=Message(role='tool', tool_call_id=tool_call_id, content=json_str), documents=documents)
        except Exception as e:
            self.logger.error(f"Something went wrong with the RAG: {e}")
            raise RagClientFailedError("The RAG client failed") from e
    
    def _validate_filter(self, arguments: dict):
        raw_metadata_filter = arguments.get("metadata_filter")
        if not raw_metadata_filter:
            self.logger.warning(f"No metadata filter provided.")
            raise MetadataFilterError(f"No metadata filter provided.")
        
        primary_key, primary_value = next(iter(raw_metadata_filter.items()))
        metadata_filter = {primary_key: primary_value}
        allowed = {"article", "chapter", "section"}
        unexpected = set(metadata_filter.keys()) - allowed

        if unexpected:
            raise ValueError(f"Unexpected metadata keys: {unexpected}")

        for k, v in metadata_filter.items():
            if not isinstance(v, int):
                raise TypeError(f"Metadata value for {k} must be int, got {type(v)}")

        return metadata_filter

    def _query(
        self,
        query_embedding: list[float],
        collection: str, 
        ) -> list[ChromaDbResult]:
        chroma_client = chromadb.HttpClient(
            host=self.configs.chromadb_host, 
            port=self.configs.chromadb_port
            )
        col = chroma_client.get_collection(name=collection)
        raw = col.query(
            query_embeddings=[query_embedding], 
            n_results=self.configs.chroma_top_n,
            include=["documents", "metadatas",]
            )
        return self._format_query_result(raw)
    
    def _get(
        self,
        metadata_filter: dict,
        collection: str, 
        ) -> list[ChromaDbResult]:
        chroma_client = chromadb.HttpClient(
            host=self.configs.chromadb_host, 
            port=self.configs.chromadb_port
            )
        col = chroma_client.get_collection(name=collection)
        raw = col.get(
            where=metadata_filter,
            include=["documents", "metadatas",]
            )
        return self._format_get_result(raw)

    def _format_query_result(self, raw: dict) -> list[ChromaDbResult]:
        results = [ChromaDbResult(
            id=raw["ids"][0][i],
            document=raw["documents"][0][i], 
            metadata=raw["metadatas"][0][i],
            ) for i in range(len(raw["ids"][0]))]
        return results
    
    def _format_get_result(self, raw: dict) -> list[ChromaDbResult]:
        results = [ChromaDbResult(
            id=raw["ids"][i],
            document=raw["documents"][i], 
            metadata=raw["metadatas"][i],
        ) for i in range(len(raw["ids"]))]
        return results

    def _filter_results(
            self,
            results: list[ChromaDbResult], 
            reranked: RerankResponse,
            ) -> list[ChromaDbResult]:
        filtered_results = []

        for item in reranked.results:
            for result in results:
                if result.id == item.id:
                    filtered_results.append(result)
        return filtered_results