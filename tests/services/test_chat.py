import pytest, logging, json
from unittest.mock import MagicMock
from app.services.chat import Chat
from app.core.config import Configurations
from app.models import *

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.name = "user_1"
    user.id = 1
    return user

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.create_chat.return_value = 1
    mock_message = Message(role='system', content="system prompt")
    db.get_messages.return_value = [
        (json.dumps(mock_message.model_dump()), None)
        ]
    return db

@pytest.fixture
def existing_chat(fake_logger, fake_configs, mock_db, mock_user):
    return Chat(logger=fake_logger, user=mock_user, db=mock_db, configs=fake_configs)

def test_chat_instantiate_chat(fake_logger, fake_configs, mock_db, mock_user):
    new_chat = Chat(logger=fake_logger, user=mock_user, db=mock_db, configs=fake_configs)
    assert len(new_chat.messages) == 1
    assert new_chat.user.id == 1
    assert new_chat.user.name == "user_1"
    
def test_chat_add_message(existing_chat):
    message = MessageDocuments(message=Message(role="user", content="Content goes here."))
    existing_chat.add_message(message)
    assert len(existing_chat.messages) == 2

def test_instantiate_chat_with_existing_id(fake_configs, db_factory, fake_logger, mock_user):
    fake_db = db_factory()
    chat = Chat(logger=fake_logger, user=mock_user, db=fake_db, configs=fake_configs, chat_id=1)
    fake_msg_docs = chat.messages[0]
    assert fake_msg_docs.message.content == "fake prompt"