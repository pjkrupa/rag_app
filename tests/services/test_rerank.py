import pytest, logging
from app.services.embeddings import EmbeddingsClient
from app.models import *
from app.core.config import Configurations

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
mock_configs = Configurations.from_model(logger=mock_logger, configs_model=configs)

@pytest.fixture
def embeder():
    return EmbeddingsClient(configs=mock_configs)

def test_rerank_payload(embeder):
    mock_results = [ChromaDbResult(id="id", document="test document", metadata={"chapter": 1}, distance=2)]
    mock_query_text = "query text here"
    result = embeder._build_rerank_payload(query_text=mock_query_text, results=mock_results)
    assert result["query"] == "query text here"
    assert result["items"][0]["text"] == "test document"
    assert result["top_n"] == embeder.configs.rerank_top_n