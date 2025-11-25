import pytest, logging,json
from unittest.mock import patch, MagicMock
from functions import Chat, EmbeddingsClient, LlmClient, ToolHandler
from models import *
from logging_setup import get_logger

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
]

mock_tools = [Tool(type="function", function=FunctionDefinition.model_validate(tool)) for tool in MOCK_TOOLS]

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
        rerank_top_n=3
    )

@pytest.fixture
def chat():
    return Chat(configs=mock_configs)

@pytest.fixture
def embeder():
    return EmbeddingsClient(configs=mock_configs)

@pytest.fixture
def llm_client():
    return LlmClient(configs=mock_configs, tools=mock_tools)

@pytest.fixture
def tools_client():
    return ToolHandler(configs=mock_configs, tools=mock_tools)

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

def test_rerank_payload(embeder):
    mock_results = [ChromaDbResult(id="id", document="test document", metadata={"chapter": 1}, distance=2)]
    mock_query_text = "query text here"
    result = embeder._build_rerank_payload(query_text=mock_query_text, results=mock_results)
    assert result["query"] == "query text here"
    assert result["items"][0]["text"] == "test document"
    assert result["top_n"] == embeder.configs.rerank_top_n

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

def test_tools_client_handle(tools_client):
    fake_function_call = FunctionCall(name="gdpr_query", arguments=json.dumps({"query_text": "test query text"}))
    fake_tool_call = ToolCall(id="1234", type="function", function=fake_function_call)
    fake_message = Message(role="user", content="test content", tool_calls=[fake_tool_call])

    result = tools_client.handle(fake_message)