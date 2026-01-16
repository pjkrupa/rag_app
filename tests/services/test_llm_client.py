import pytest
from unittest.mock import MagicMock
from rag_app.app.services.llm_client import LlmClient
from rag_app.app.models import Message

@pytest.fixture
def llm_client(fake_configs):
    return LlmClient(configs=fake_configs)

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