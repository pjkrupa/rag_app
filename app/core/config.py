from dataclasses import dataclass
from logging import Logger
import os

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
    sqlite_path: str

def set_configs(logger: Logger):
    configs = Configurations(
        model=os.getenv("MODEL"),
        ollama_api_base=os.getenv("OLLAMA_URL"),
        system_prompt=os.getenv("SYSTEM_PROMPT"),
        logger=logger,
        chromadb_host=os.getenv("CHROMADB_HOST"),
        chromadb_port=int(os.getenv("CHROMADB_PORT")),
        embeddings_url=os.getenv("EMBEDDINGS_URL"),
        chroma_top_n=int(os.getenv("CHROMA_TOP_N")),
        rerank_top_n=int(os.getenv("RERANK_TOP_N")),
        sqlite_path=os.getenv("SQLITE_PATH")
    )
    return configs