import pytest, logging, uuid, json, time
from app.core.config import Configurations
from app.services.db_manager import DatabaseManager
from app.models import *

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
    
@pytest.fixture
def db_factory(fake_configs, fake_messages):
    """
    Returns a function that constructs a fresh, populated DatabaseManager.
    Tests call: db = db_factory()
    """
    def _make_db():
        fake_db = DatabaseManager(configs=fake_configs)
        ts = int(time.time())
        with fake_db._get_conn() as conn:
            cursor = conn.cursor()

            # generate the fake records
            # user and chat ids will be 1
            cursor.execute(
                """
                INSERT INTO users (user_name, created_at)
                VALUES (?, ?)
                """,
                ("peter", ts)
                )
            user_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO chats (user_id, created_at, updated_at)
                VALUES (?, ?, ?)
                """,
                (user_id, ts, ts)
                )
            chat_id = cursor.lastrowid

            msg_blob = fake_messages.message.model_dump_json()
            docs_blob = json.dumps([d.model_dump() for d in fake_messages.documents])
            
            cursor.execute(
                """
                INSERT INTO messages (chat_id, message, documents, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (chat_id, msg_blob, docs_blob, ts)
                )
        return fake_db
            
    return _make_db


