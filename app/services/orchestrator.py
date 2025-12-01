from app.core.config import Configurations
from app.services.user import User, UserNotFoundError
from app.services.db_manager import DatabaseManager
from app.services.chat import Chat
from app.services.llm_client import LlmClient
from app.models import *
from app.tools.registry import TOOLS
from app.services.tool_handler import ToolHandler


class Orchestrator:
    def __init__(self, configs: Configurations):
        self.configs = configs
        self.db = DatabaseManager(configs=configs)
        self.logger = self.configs.logger
        self.user = None
        self.chat = None
        tools = [Tool(type="function", function=FunctionDefinition.model_validate(tool)) for tool in TOOLS]
        self.llm_client = LlmClient(configs=configs, tools=tools)
        self.tool_client = ToolHandler(configs=configs, tools=tools)

    def get_user_name(self, user_name: str):
        try:
            self.user = User(configs=self.configs, db=self.db, user_name=user_name)
            self.chat = Chat(user=self.user, db=self.db, configs=self.configs)
            return self.user
        except UserNotFoundError as e:
            self.logger.error(f"{e}")
            return None
    
    def create_user(self, user_name: str):
        self.db.create_user(user_name=user_name)
        self.user = User(configs=self.configs, db=self.db, user_name=user_name)
        self.chat = Chat(user=self.user, db=self.db, configs=self.configs)
        self.logger.info(f"Created user {user_name}.")

    def process_prompt(self, prompt: str) -> str:
        self.chat.add_message(Message(role="user", content=prompt))
        response = self.llm_client.send_request(messages=self.chat.messages)
        response_message = self.llm_client.get_messsage(response=response)

        # Check if the model called a tool:
        if response_message.tool_calls:
            # call the tool and get the result as a Message...
            tool_message = self.tool_client.handle(response_message)
            # ... add the message to the chat
            self.chat.add_message(tool_message)
            # ... and resend the chat to the LLM:
            tool_response = self.llm_client.send_request(messages=self.chat.messages)

            # then pull the message from the response, add it to the chat, and deliver it to the user.
            final_response_message = self.llm_client.get_messsage(response=tool_response)
            self.chat.add_message(final_response_message)
            return final_response_message.content
        else:
            self.chat.add_message(response_message)
            return response_message.content