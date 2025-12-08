import pytest, logging, json, uuid
from unittest.mock import patch, MagicMock
from app.core.config import Configurations
from app.services.db_manager import DatabaseManager
from app.services.chat import Chat
from app.services.user import User
from app.models import *


mock_logger = logging.getLogger(name="mock_logger")
mock_logger.setLevel(level=logging.INFO)
mock_logger.addHandler(logging.StreamHandler())



@pytest.fixture
def mock_configs():

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
    mock_configs = Configurations.from_model(logger=mock_logger, configs_model=configs)
    return mock_configs

def test_table_creation(mock_configs):
    db = DatabaseManager(mock_configs)
    with db._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_list = [r[0] for r in cursor.fetchall()]
        assert "users" in tables_list
        assert "chats" in tables_list
        assert "messages" in tables_list

def test_create_user(mock_configs):
    db = DatabaseManager(mock_configs)
    with db._get_conn() as conn:
        cursor = conn.cursor()
        db.create_user("test_user")
        cursor.execute("SELECT * FROM users WHERE user_name = ?", ("test_user",))
        row = cursor.fetchone()
        assert row[1] == "test_user"

    
def test_check_user_valid(mock_configs):
    db = DatabaseManager(mock_configs)
    db.create_user("test_user")
    user_id = db.check_user("test_user")
    assert user_id
    assert user_id > 0

def test_check_user_invalid(mock_configs):
    db = DatabaseManager(mock_configs)
    db.create_user("test_user")
    user_id = db.check_user("invalid_user")
    assert user_id is None

def test_create_chat(mock_configs):
    db = DatabaseManager(mock_configs)
    db.create_user("test_user")
    user_id = db.check_user("test_user")
    mock_message = MessageDocuments(
        message=Message(
            role='system', 
            content="system prompt"
            ), 
        documents=[
            ChromaDbResult(
                id="id", 
                document="document", 
                metadata={"key": "value"},
                distance=1.1
                )
            ]
        )
    mock_message_blob = json.dumps(mock_message.message.model_dump())
    mock_documents_blob = json.dumps([doc.model_dump() for doc in mock_message.documents])
    with db._get_conn() as conn:
        cursor = conn.cursor()
        chat_id = db.create_chat(user_id=1, init_message=mock_message)
        cursor.execute("SELECT message, documents FROM messages WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        assert chat_id > 0
        assert row[0] == mock_message_blob
        assert row[1] == mock_documents_blob

def test_insert_message(mock_configs):
    db = DatabaseManager(mock_configs)
    db.create_user("test_user")
    user = User(configs=mock_configs, db=db, user_name="test_user")
    mock_message = Message(role='system', content="system prompt")
    mock_msg_docs = MessageDocuments(message=mock_message)
    chat_id = db.create_chat(user_id=user.id, init_message=mock_msg_docs)
    
    # make an updated message and insert it in the database
    updated_message = MessageDocuments(message=Message(role='user', content="updated message"))
    db.insert_message(chat_id=chat_id, msg_docs=updated_message)

    # create test blob
    msgs = [mock_msg_docs, updated_message]
    blob = json.dumps([m.model_dump() for m in msgs])
    
    # get the updated blob from the database and compare it to test blob
    with db._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message FROM messages WHERE chat_id=?", (chat_id,))
        rows = cursor.fetchall()
        msg_blob = json.dumps([
            MessageDocuments(
                message=Message(**json.loads(row[0]))
                ).model_dump(mode="json")
                for row in rows
                ])
        assert msg_blob == blob

def test_get_messages(mock_configs):
    db = DatabaseManager(mock_configs)
    # create the user and the messages
    db.create_user("test_user")
    user = User(configs=mock_configs, db=db, user_name="test_user")
    mock_message = MessageDocuments(message=Message(role='system', content="system prompt"))
    mock_blob = json.dumps([mock_message.model_dump()])
    chat_id = db.create_chat(user_id=user.id, init_message=mock_message)

    # use the method to get the messages from the db
    messages = db.get_messages(chat_id=chat_id)
    test_message = MessageDocuments(message=Message(**json.loads(messages[0][0])))
    message_blob = json.dumps([test_message.model_dump()])
    assert mock_blob == message_blob
