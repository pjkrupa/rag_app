import pytest
from unittest.mock import patch, MagicMock
from functions import Chat, EmbeddingsClient
from models import *
from logging_setup import get_logger


logger = get_logger()

mock_configs = Configurations(
        model="llama",
        ollama_api_base="http://localhost:11434",
        system_prompt="system prompt",
        logger=logger,
        chromadb_host="http://localhost",
        chromadb_port=8000,
        embeddings_url="http://localhost:8001",
        chroma_top_n=10,
        rerank_top_n=3
    )

@pytest.fixture
def chat():
    return Chat(configs=mock_configs)

@pytest.fixture
def embeder():
    return EmbeddingsClient(configs=mock_configs)

def test_chat_instantiate_chat(chat):
    assert len(chat.messages) == 1
    
def test_chat_add_message(chat):
    message = Message(role="user", content="Content goes here.")
    chat.add_message(message)
    assert len(chat.messages) == 2

def test_embedder_output(embeder):
    fake_embedding = [0.1, 0.2, 0.3]
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"embedding": fake_embedding}
    mock_resp.status_code = 200
    with patch("functions.requests.post", return_value=mock_resp):
        result = embeder.embed("test text")
    assert result == fake_embedding

