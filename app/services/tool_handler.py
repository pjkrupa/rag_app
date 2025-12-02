import json
from app.core.config import Configurations
from app.models import Tool, Message, FunctionDefinition
from app.services.rag import RagClient
from app.tools.registry import TOOLS
from app.models import ChromaDbResult

class ToolHandler:

    def __init__(self, configs: Configurations):
        self.configs = configs
        self.tool_chain = self._make_tool_chain(TOOLS=TOOLS)
        self.tool_names = list(self.tool_chain.keys())
        self.logger = configs.logger
        self.rag = RagClient(configs)

    def _make_tool_chain(self, TOOLS: list[dict]) -> dict[str:Tool]:
        tools = [Tool(type="function", function=FunctionDefinition.model_validate(tool)) for tool in TOOLS]
        return {tool.function.name: tool for tool in tools}
    
    def handle(self, message: Message) -> tuple[Message, list[ChromaDbResult]]:
        for tool_call in message.tool_calls:

            if tool_call.function.name not in self.tool_names:
                self.logger.error(f"The model tried to call tool {tool_call.function.name}, which is not in the list of tool names: {self.tool_names} ")
                return Message(role='tool', tool_call_id=tool_call.id, content='There is no tool with that name.')
            
            # need an elif block for each name in tool_names
            elif tool_call.function.name == "gdpr_query":
                arguments = json.loads(tool_call.function.arguments)
                self.logger.info(f"Call for tool {tool_call.function.name}: {arguments}")
                return self.rag.generate( 
                    query=arguments["query_text"], 
                    tool_call_id=message.tool_call_id, 
                    collection="gdpr")
            
            # logs an error if a tool exists but handling hasn't been added yet
            else:
                self.logger.error(f"Tool call for {tool_call.function.name} not handled. Have you added handling for it yet??")
                return Message(role='tool', tool_call_id=tool_call.id, content='Tool not found.')