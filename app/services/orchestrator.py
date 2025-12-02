from app.core.config import Configurations
from app.services.user import User
from app.services.db_manager import DatabaseManager
from app.services.chat import Chat
from app.services.llm_client import LlmClient
from app.models import *
from app.core.errors import *
from app.services.tool_handler import ToolHandler


class Orchestrator:
    def __init__(self, configs: Configurations):
        self.configs = configs
        self.db = DatabaseManager(configs=configs)
        self.logger = self.configs.logger
        self.user = None
        self.chat = None
        self.llm_client = LlmClient(configs=configs)
        self.tool_client = ToolHandler(configs=configs)

    def get_user_name(self, user_name: str):
        while True:
            try:
                self.user = User(configs=self.configs, db=self.db, user_name=user_name)
                self.chat = Chat(user=self.user, db=self.db, configs=self.configs)
                return
            except UserNotFoundError as e:
                self.logger.error(f"User not found: {e}")
                user_name = input("Enter your user name>> ")
                continue
    
    def create_user(self, user_name: str):
        while True:
            try:
                self.db.create_user(user_name=user_name)
                self.user = User(configs=self.configs, db=self.db, user_name=user_name)
                self.chat = Chat(user=self.user, db=self.db, configs=self.configs)
                self.logger.info(f"Created user {user_name}.")
                return
            except UserAlreadyExistsError as e:
                self.logger.error(f"User already exists: {e}")
                user_name = input("Select a user name>> ")
                continue

    # checks to see if user attached a tool to the prompt with --<tool>
    def _parse_prompt(self, prompt: str) -> tuple[str, Tool | None]:
        if "--" not in prompt:
            return prompt, None
        prompt, tool_name = (part.strip() for part in prompt.split("--", 1))
        if tool_name not in self.tool_client.tool_names:
            self.logger.error(f"Tool name not found: {tool_name}")
            return prompt, None
        return prompt, self.tool_client.tool_chain[tool_name]
        
    def process_prompt(self, prompt: str) -> tuple[Message, list[ChromaDbResult]]:
        prompt, tool = self._parse_prompt(prompt)
        self.chat.add_message(Message(role="user", content=prompt))
        response = self.llm_client.send_request(messages=self.chat.messages, tool=tool)
        response_message = self.llm_client.get_messsage(response=response)

        # Check if the model called a tool:
        if response_message.tool_calls:
            # call the tool and get the result as a Message, plus a list of ChromaDbResult objects...
            tool_message, documents = self.tool_client.handle(response_message)
            # ... add the message to the chat
            self.chat.add_message(tool_message)
            # ... and resend the chat to the LLM:
            tool_response = self.llm_client.send_request(messages=self.chat.messages)

            # then pull the message from the response, add it to the chat, and deliver it to the user.
            final_response_message = self.llm_client.get_messsage(response=tool_response)
            self.chat.add_message(final_response_message)
            return final_response_message, documents
        else:
            self.chat.add_message(response_message)
            return response_message, None