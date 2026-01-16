import pytest, logging
from rag_app.app.services.embeddings import EmbeddingsClient
from rag_app.app.models import *
from rag_app.app.core.config import Configurations

# configs = ConfigurationsModel(
#         model="llama",
#         api_base="http://localhost:11434",
#         chromadb_host="http://localhost",
#         chromadb_port=8000,
#         embeddings_url="http://localhost:8001",
#         chroma_top_n=10,
#         rerank_top_n=3,
#         sqlite_path="test.db",
#         system_prompt="system prompt"
#     )

@pytest.fixture
def embeder(fake_configs):
    return EmbeddingsClient(configs=fake_configs)

def test_rerank_payload(embeder):
    mock_results = [ChromaDbResult(id="id", document="test document", metadata={"chapter": 1}, distance=2)]
    mock_query_text = "query text here"
    result = embeder._build_rerank_payload(query_text=mock_query_text, results=mock_results)
    assert result["query"] == "query text here"
    assert result["items"][0]["text"] == "test document"
    assert result["top_n"] == embeder.configs.rerank_top_n