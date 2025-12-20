import json
from app.core.config import Configurations
from app.core.errors import MetadataFilterError, RagClientFailedError
from app.models import Tool, Message, FunctionDefinition
from app.services.rag import RagClient
from app.tools.registry import TOOLS
from app.models import MessageDocuments

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
    
    def handle(self, message: Message) -> list[MessageDocuments]:
        tool_messages = []
        for tool_call in message.tool_calls:

            if tool_call.function.name not in self.tool_names:
                self.logger.error(f"The model tried to call tool {tool_call.function.name}, which is not in the list of tool names: {self.tool_names} ")
                msg_docs = MessageDocuments(message=Message(role='tool', tool_call_id=tool_call.id, content='There is no tool with that name.'))
                tool_messages.append(msg_docs)
            
            # need an elif block for each name in tool_names
            elif tool_call.function.name == "gdpr_query":
                arguments = json.loads(tool_call.function.arguments)
                self.logger.info(f"Call for tool {tool_call.function.name}: {arguments}")
                try:
                    msg_docs = self.rag.chroma_query( 
                        arguments=arguments,
                        tool_call_id=tool_call.id,
                        collection="gdpr")
                except RagClientFailedError as e:
                    msg_docs = MessageDocuments(
                        message=Message(
                            role="tool", tool_call_id=tool_call.id, content=str(e),))
                tool_messages.append(msg_docs)
            
            elif tool_call.function.name == "gdpr_get":
                arguments = json.loads(tool_call.function.arguments)
                self.logger.info(f"Call for tool {tool_call.function.name}: {arguments}")
                try:
                    msg_docs = self.rag.chroma_get( 
                        arguments=arguments,
                        tool_call_id=tool_call.id,
                        collection="gdpr")
                except MetadataFilterError as e:
                    self.logger.error(f"Problem with the metadata filter: {e}")
                    msg_docs = MessageDocuments(
                        message=Message(
                            role="tool", tool_call_id=tool_call.id, content=str(e),))
                except RagClientFailedError as e:
                    msg_docs = MessageDocuments(
                        message=Message(
                            role="tool", tool_call_id=tool_call.id, content=str(e),))
                tool_messages.append(msg_docs)
            
            elif tool_call.function.name == "edpb_query":
                arguments = json.loads(tool_call.function.arguments)
                self.logger.info(f"Call for tool {tool_call.function.name}: {arguments}")
                try:
                    msg_docs = self.rag.chroma_query( 
                        arguments=arguments,
                        tool_call_id=tool_call.id,
                        collection="edpb_guidance")
                except RagClientFailedError as e:
                    msg_docs = MessageDocuments(
                        message=Message(
                            role="tool", tool_call_id=tool_call.id, content=str(e),))
                tool_messages.append(msg_docs)

            # logs an error if a tool exists but handling hasn't been added yet
            else:
                self.logger.error(f"Tool call for {tool_call.function.name} not handled. Have you added handling for it yet??")
                msg_docs = MessageDocuments(message=Message(role='tool', tool_call_id=tool_call.id, content='Tool not found.'))
                tool_messages.append(msg_docs)
        
        return tool_messages