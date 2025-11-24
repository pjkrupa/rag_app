import pytest
from functions import Chat
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

def test_instantiate_chat(chat):
    assert len(chat.messages) == 1
    
def test_add_message(chat):
    message = Message(role="user", content="Content goes here.")
    chat.add_message(message)
    assert len(chat.messages) == 2