import pytest, logging,json
from unittest.mock import patch, MagicMock
from app.core.config import Configurations
from app.services.db_manager import DatabaseManager
from app.services.chat import Chat
from app.services.user import User
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
        sqlite_path=":memory:" # makes the db run in memory so i'm testing against fresh tables every time.
    )

@pytest.fixture
def db():
    return DatabaseManager(mock_configs)

def test_table_creation(db):
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables_list = [r[0] for r in cursor.fetchall()]
    assert "users" in tables_list
    assert "chats" in tables_list
    assert "messages" in tables_list

def test_create_user(db):
    cursor = db.conn.cursor()
    db.create_user("test_user")
    cursor.execute("SELECT * FROM users WHERE user_name = ?", ("test_user",))
    row = cursor.fetchone()
    assert row[1] == "test_user"

    
def test_check_user_valid(db):
    db.create_user("test_user")
    user_id = db.check_user("test_user")
    assert user_id
    assert user_id > 0

def test_check_user_invalid(db):
    db.create_user("test_user")
    user_id = db.check_user("invalid_user")
    assert user_id is None

def test_create_chat(db):
    db.create_user("test_user")
    user_id = db.check_user("test_user")
    mock_message = Message(role='system', content="system prompt")
    mock_blob = json.dumps(mock_message.model_dump())
    cursor = db.conn.cursor()
    chat_id = db.create_chat(user_id=1, init_message=mock_message)
    cursor.execute("SELECT message, documents FROM messages WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    assert chat_id > 0
    assert row[0] == mock_blob
    assert row[1] is None

def test_insert_message(db):
    db.create_user("test_user")
    user = User(configs=mock_configs, db=db, user_name="test_user")
    mock_message = Message(role='system', content="system prompt")
    chat_id = db.create_chat(user_id=user.id, init_message=mock_message)
    
    # make an updated message and insert it in the database
    updated_message = Message(role='user', content="updated message")
    db.insert_message(chat_id=chat_id, message=updated_message)

    # create test blob
    msgs = [mock_message, updated_message]
    blob = json.dumps([m.model_dump() for m in msgs])
    
    # get the updated blob from the database and compare it to test blob
    cursor = db.conn.cursor()
    cursor.execute("SELECT message FROM messages WHERE chat_id=?", (chat_id,))
    rows = cursor.fetchall()
    msg_blob = json.dumps([Message(**json.loads(row[0])).model_dump() for row in rows])

    assert msg_blob == blob

def test_get_messages(db):
    # create the user and the messages
    db.create_user("test_user")
    user = User(configs=mock_configs, db=db, user_name="test_user")
    mock_message = Message(role='system', content="system prompt")
    mock_blob = json.dumps([mock_message.model_dump()])
    chat_id = db.create_chat(user_id=user.id, init_message=mock_message)

    # use the method to get the messages from the db
    messages = db.get_messages(chat_id=chat_id)

    # get messages to test against
    cursor = db.conn.cursor()
    cursor.execute("SELECT message, documents FROM messages WHERE id = ?", (chat_id,))
    rows = cursor.fetchall()
    assert rows == messages
