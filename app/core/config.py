from dataclasses import dataclass
from logging import Logger

@dataclass
class Configurations:
    model: str
    ollama_api_base: str
    system_prompt: str
    logger: Logger
    chromadb_host: str
    chromadb_port: int
    embeddings_url: str
    chroma_top_n: int
    rerank_top_n: int