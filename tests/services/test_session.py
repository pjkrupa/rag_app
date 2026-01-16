import logging
from logging import Logger
from rag_app.app.services.session import Session
from rag_app.app.services.llm_client import LlmClient
from rag_app.app.services.db_manager import DatabaseManager
from rag_app.app.services.tool_handler import ToolHandler
from rag_app.app.models import Tool, FunctionDefinition

# checks the init to make sure chat and user are None and everything else loads as expected.
def test_init_session(fake_configs):
    session = Session(configs=fake_configs)
    assert session.chat is None
    assert session.user is None
    assert isinstance(session.id, str)
    assert isinstance(session.logger, Logger)
    assert isinstance(session.db, DatabaseManager)
    assert isinstance(session.llm_client, LlmClient)
    assert isinstance(session.tool_client, ToolHandler)

def test__get_tools_success(fake_configs):
    fake_tool_chain = {
        "fake_tool": Tool(
            type="fake", 
            function=FunctionDefinition(
                name="fake_tool", 
                description="", 
                parameters={"foo": "bar"}
            )
        )
    }
    session = Session(configs=fake_configs)
    session.tool_client.tool_chain = fake_tool_chain
    fake_tools = session._get_tools(["fake_tool"])
    assert isinstance(fake_tools, list)
    assert isinstance(fake_tools[0], Tool)
    assert fake_tools[0].function.name == "fake_tool"

def test__get_tools_failure(fake_configs, caplog):
    fake_tool_chain = {
        "fake_tool": Tool(
            type="fake", 
            function=FunctionDefinition(
                name="fake_tool", 
                description="", 
                parameters={"foo": "bar"}
            )
        )
    }
    session = Session(configs=fake_configs)
    session.tool_client.tool_chain = fake_tool_chain

    with caplog.at_level(logging.ERROR):
        fake_tools = session._get_tools(["fake_tool", "bad_tool"])
    
    assert len(fake_tools) == 1
    assert fake_tools[0].function.name == "fake_tool"
    assert "Tool bad_tool not found on the tool chain." in caplog.text


# class FunctionDefinition(BaseModel):
#     name: str
#     description: str = ""
#     parameters: dict[str, Any]

# class Tool(BaseModel):
#     type: str = "function"
#     function: FunctionDefinition
