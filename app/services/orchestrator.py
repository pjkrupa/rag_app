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

    def default_user(self,):
        try:
            self.db.create_user(user_name="default")
        except UserAlreadyExistsError as e:
            self.logger.info(f"Default user already exists, starting session...")
        self.user = User(configs=self.configs, db=self.db, user_name="default")
        self.chat = Chat(user=self.user, db=self.db, configs=self.configs)

    def cli_get_user_name(self, user_name: str):
        while True:
            try:
                self.user = User(configs=self.configs, db=self.db, user_name=user_name)
                self.chat = Chat(user=self.user, db=self.db, configs=self.configs)
                return
            except UserNotFoundError as e:
                self.logger.error(f"User not found: {e}")
                user_name = input("Enter your user name>> ")
                continue
    
    def cli_create_user(self, user_name: str):
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
    def _parse_prompt(self, prompt: str) -> tuple[str, Tool | None | str]:
        if "--" not in prompt:
            return prompt, None
        prompt, tool_name = (part.strip() for part in prompt.split("--", 1))
        if tool_name not in self.tool_client.tool_names:
            self.logger.error(f"Tool not found: '{tool_name}'")
            raise ToolParseError(f"Tool not found: '{tool_name}'")
        return prompt, self.tool_client.tool_chain[tool_name]
    
    def _fail(self, msg: str):
        self.logger.error(msg)
        return Message(role="assistant", content=msg), None

    def _run_tool_flow(self, response_message: Message) -> tuple[Message, Tool | None]:
        
        # call the tool (RAG client), get: 
        #   1) the message to return to the LLM, 
        #   2) the documents returned by the RAG client
        for tool_call in response_message.tool_calls:
            self.logger.info(f"Tool call! name: {tool_call.function.name}, arguments: {tool_call.function.arguments}")
        try:
            tool_message, documents = self.tool_client.handle(response_message)
        except RagClientFailedError as e:
            return self._fail(f"RAG client failed: {e}")
        self.logger.info(tool_message)
        self.logger.info(documents)

        self.chat.add_message(tool_message)

        # send the query with the context gathered from the RAG client
        try:
            tool_response = self.llm_client.send_request(messages=self.chat.messages)
        except LlmCallFailedError as e:
            return self._fail(f"LLM call failed: {e}")

        # then pull the message from the response, add it to the chat, and deliver it to the user,
        # along with the documents/metadata returned by the RAG client.
        final_response_message = self.llm_client.get_messsage(response=tool_response)
        self.chat.add_message(final_response_message)
        return final_response_message, documents
    
    def process_prompt(self, prompt: str) -> tuple[Message, list[ChromaDbResult] | None]:
        # check for tool calling
        try:
            prompt, tool = self._parse_prompt(prompt)
        except ToolParseError:
            return (
            Message(role="assistant", content="Sorry, that tool could not be found. Please select a valid tool."),
            None,
            )
        self.chat.add_message(Message(role="user", content=prompt))
        
        self.logger.info(f"User: {prompt}")
        # intial call to the LLM
        try:
            response = self.llm_client.send_request(messages=self.chat.messages, tool=tool)
        except LlmCallFailedError as e:
            return self._fail(f"LLM call failed: {e}")
        response_message = self.llm_client.get_messsage(response=response)
        
        if not response_message.tool_calls:
            self.chat.add_message(response_message)
            self.logger.info(f"Assistant: {response_message.content}")
            return response_message, None

        return self._run_tool_flow(response_message)
        
        