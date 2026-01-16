import pytest, logging, uuid, json, time
from rag_app.app.core.config import Configurations
from rag_app.app.services.db_manager import DatabaseManager
from rag_app.app.models import *

@pytest.fixture
def fake_tools():
    FAKE_TOOLS = [
    {"name": "gdpr_query",
     "description": "Description of my tool.",
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
    return [Tool(type="function", function=FunctionDefinition.model_validate(tool)) for tool in FAKE_TOOLS]

@pytest.fixture
def fake_messages():
    fake_message = Message(role="user", content="fake prompt")
    fake_documents = [
        ChromaDbResult(
        id="abc", 
        document="fake document1", 
        metadata={"fake": "metadata1"}, 
        distance=1.1,
        ),
        ChromaDbResult(
        id="def", 
        document="fake document2", 
        metadata={"fake": "metadata2"}, 
        distance=1.2,
        )
        ]
    return MessageDocuments(message=fake_message, documents=fake_documents)
    
@pytest.fixture
def fake_logger():
    fake_logger = logging.getLogger(name="fake_logger")
    fake_logger.setLevel(level=logging.INFO)
    fake_logger.addHandler(logging.StreamHandler())
    return fake_logger

@pytest.fixture
def fake_configs(fake_logger):
    unique_db = f"file:memdb_{uuid.uuid4().hex}?mode=memory&cache=shared"

    configs = ConfigurationsModel(
        model="llama",
        api_base="http://localhost:11434",
        chromadb_host="http://localhost",
        chromadb_port=8000,
        embeddings_url="http://localhost:8001",
        chroma_top_n=10,
        rerank_top_n=3,
        sqlite_path=unique_db,
        system_prompt="system prompt"
    )
    return Configurations.from_model(logger=fake_logger, configs_model=configs)


