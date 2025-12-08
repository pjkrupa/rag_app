import pytest, logging
from unittest.mock import patch, MagicMock
from app.core.config import Configurations
from app.services.embeddings import EmbeddingsClient
from app.models import *

MOCK_TOOLS = [
    {"name": "gdpr_query",
     "description": "Description of my mock tool.",
     "parameters": {
        "type": "object",
        "properties": {
            "query_text": {
                "type": "string",
                "description": "query string goes here."
            }
        },
    "required": ["query_text"]
}
    },
    {"name": "fake_tool",
     "description": "Description of my fake tool.",
     "parameters": {
        "type": "object",
        "properties": {
            "query_text": {
                "type": "string",
                "description": "query string goes here."
            }
        },
    "required": ["query_text"]
}
    }
]

mock_tools = [Tool(type="function", function=FunctionDefinition.model_validate(tool)) for tool in MOCK_TOOLS]

mock_logger = logging.getLogger(name="mock_logger")
mock_logger.setLevel(level=logging.INFO)
mock_logger.addHandler(logging.StreamHandler())

configs = ConfigurationsModel(
        model="llama",
        api_base="http://localhost:11434",
        chromadb_host="http://localhost",
        chromadb_port=8000,
        embeddings_url="http://localhost:8001",
        chroma_top_n=10,
        rerank_top_n=3,
        sqlite_path="test.db",
        system_prompt="system prompt"
    )
mock_configs = Configurations.from_model(logger=mock_logger, model=configs)

@pytest.fixture
def embeder():
    return EmbeddingsClient(configs=mock_configs)

def test_embedder_output(embeder):
    fake_embedding = [0.1, 0.2, 0.3]
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"embedding": fake_embedding}
    mock_resp.status_code = 200
    with patch("app.services.embeddings.requests.post", return_value=mock_resp):
        result = embeder.embed("test text")
    assert result == fake_embedding