from rag_app.app.tools.registry import TOOLS
import pytest, logging,json
from unittest.mock import patch, MagicMock
from rag_app.app.core.config import Configurations
from rag_app.app.services.chat import Chat
from rag_app.app.services.user import User
from rag_app.app.services.embeddings import EmbeddingsClient
from rag_app.app.services.llm_client import LlmClient
from rag_app.app.services.tool_handler import ToolHandler
import rag_app.app.services.tool_handler as toolhandler_module
from rag_app.app.services.db_manager import DatabaseManager
from rag_app.app.models import *

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
mock_tool_chain = {tool.function.name: tool for tool in mock_tools}

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
mock_configs = Configurations.from_model(logger=mock_logger, configs_model=configs)

# write some tests to validate the tools included in TOOLS... JSON schema, structure, etc.

@pytest.fixture
def tools_client():
    with patch.object(toolhandler_module, "TOOLS", MOCK_TOOLS):
        yield ToolHandler(configs=mock_configs)

def test_tools_client_handle_undefined_tool(tools_client):
    fake_function_call = FunctionCall(name="fake_tool", arguments=json.dumps({"query_text": "test query text"}))
    fake_tool_call = ToolCall(id="1234", type="function", function=fake_function_call)
    fake_message = Message(role="user", content="test content", tool_calls=[fake_tool_call])
    messages = tools_client.handle(fake_message)
    msg_docs = messages[0]
    assert msg_docs.message.content == "Tool not found."

def test_tools_client_handle_nonexistent_tool(tools_client):
    fake_function_call = FunctionCall(name="nonexistent_tool", arguments=json.dumps({"query_text": "test query text"}))
    fake_tool_call = ToolCall(id="1234", type="function", function=fake_function_call)
    fake_message = Message(role="user", content="test content", tool_calls=[fake_tool_call])
    messages = tools_client.handle(fake_message)
    msg_docs = messages[0]
    assert msg_docs.message.content == "There is no tool with that name."