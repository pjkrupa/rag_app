import pytest, logging, json
from unittest.mock import MagicMock
from app.services.chat import Chat
from app.core.config import Configurations
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
def new_chat(mock_db, mock_user):
    return Chat(configs=mock_configs, db=mock_db, chat_id=None, user=mock_user)

# need to add error handling and check it by trying to instantiate a non-existent chat.
@pytest.fixture
def existing_chat(mock_db, mock_user):
    return Chat(configs=mock_configs, db=mock_db, chat_id=2, user=mock_user)

def test_chat_instantiate_chat(new_chat):
    assert len(new_chat.messages) == 1
    assert new_chat.user.id == 1
    assert new_chat.user.name == "user_1"
    
def test_chat_add_message(existing_chat):
    message = Message(role="user", content="Content goes here.")
    existing_chat.add_message(message)
    assert len(existing_chat.messages) == 2