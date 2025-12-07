import pytest, logging
from unittest.mock import MagicMock
from app.core.config import Configurations
from app.services.llm_client import LlmClient
from app.models import *



mock_logger = logging.getLogger(name="mock_logger")
mock_logger.setLevel(level=logging.INFO)
mock_logger.addHandler(logging.StreamHandler())

mock_configs = Configurations(
        model="llama",
        ollama_api_base="http://localhost:11434",
        system_prompt="system prompt",
        logger=mock_logger,
        chromadb_host="http://localhost",
        chromadb_port=8000,
        embeddings_url="http://localhost:8001",
        chroma_top_n=10,
        rerank_top_n=3,
        sqlite_path="test.db"
    )

@pytest.fixture
def llm_client():
    return LlmClient(configs=mock_configs)

def test_llm_client_get_message(llm_client):
    fake_message_model = {"role": "user", "content": "test content"}
    mock_message = MagicMock()
    mock_message.model_dump.return_value = fake_message_model

    fake_choice = MagicMock()
    fake_choice.message = mock_message

    mock_resp = MagicMock()
    mock_resp.choices = [fake_choice]

    result = llm_client.get_messsage(mock_resp)

    assert isinstance(result, Message)
    assert result.role == "user"
    assert result.content == "test content"