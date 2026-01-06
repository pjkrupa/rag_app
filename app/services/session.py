from collections.abc import Iterator

import uuid
from app.core.config import Configurations
from app.services.user import User
from app.services.db_manager import DatabaseManager
from app.services.chat import Chat
from app.services.llm_client import LlmClient
from app.models import *
from app.core.errors import *
from app.services.tool_handler import ToolHandler


class Session:
    def __init__(self, configs: Configurations):
        self.id = str(uuid.uuid4())
        self.configs: Configurations = configs
        self.db: DatabaseManager = DatabaseManager(configs=configs)
        self.logger = self.configs.logger
        self.user: User = None
        self.chat: Chat = None
        self.llm_client: LlmClient = LlmClient(configs=configs)
        self.tool_client: ToolHandler = ToolHandler(configs=configs)
        self._log_configs()

    def _log_configs(self):
        self.logger.debug(f"System prompt: {self.configs.system_prompt}")

    def default_user(self,):
        try:
            self.db.create_user(user_name="default")
        except UserAlreadyExistsError as e:
            self.logger.info(f"Default user already exists, starting session...")
        self.user = User(configs=self.configs, db=self.db, user_name="default")
    
    def _get_tools(self, tool_names: list[str]) -> tuple[str, list[Tool]]:
        tools = []
        for tool_name in tool_names:
            try:
                tools.append(self.tool_client.tool_chain[tool_name])
            except LookupError:
                self.logger.error(f"Tool not found on the tool chain.")
        return tools
    
    def _fail(self, msg: str):
        self.logger.error(msg)
        return MessageDocuments(message=Message(role="assistant", content=msg))

    def _run_tool_flow(self, response_message: Message) -> MessageDocuments:

        # add the model's tool_call message to the chat
        self.chat.add_message(msg_docs=MessageDocuments(message=response_message))

        # call the tool (RAG client), get: 
        #   1) the message to return to the LLM, 
        #   2) the documents returned by the RAG client
        # they will be a list of MessageDocuments objects
        for tool_call in response_message.tool_calls:
            self.logger.info(f"Tool call! name: {tool_call.function.name}, arguments: {tool_call.function.arguments}")
        try:
            tool_responses = self.tool_client.handle(response_message)
        except RagClientFailedError as e:
            return self._fail(f"RAG client failed: {e}")
        
        documents = []
        for msg_docs in tool_responses:
            self.logger.info("Tool call added to chat.")
            self.logger.info(f"tool_call_id: {msg_docs.message.tool_call_id}")
            documents.extend(msg_docs.documents)
            self.chat.add_message(msg_docs=msg_docs)

        # send the query with the context gathered from the RAG client
        try:
            tool_response = self.llm_client.send_request(messages=self.chat.messages)
        except LlmCallFailedError as e:
            return self._fail(f"LLM call failed: {e}")

        # then pull the message from the response, add it to the chat, and deliver it to the user,
        # along with the documents/metadata returned by the RAG client.
        final_response_message = self.llm_client.get_messsage(response=tool_response)
        msg_docs = MessageDocuments(message=final_response_message, documents=documents)
        self.chat.add_message(msg_docs)
        return msg_docs
    
    def load_chat(self, chat_id: int):
        if not self.user:
            self.logger.error(f"User not loaded. You have to add a user to the session before you can load a chat.")
            return
        self.chat = Chat(
            logger=self.logger, 
            user=self.user, 
            db=self.db, 
            configs=self.configs, 
            chat_id=chat_id,
            )
        
    def load_user(self, user_name: str):
        self.user = User(configs=self.configs, db=self.db, user_name=user_name)

    def last_message(self) -> MessageDocuments:
        return self.chat.messages[-1]
    
    def process_prompt(
            self, 
            prompt: str, 
            tool_names: list[str] = []
        ) -> MessageDocuments:
        
        if tool_names:
            tools = self._get_tools(tool_names=tool_names)
        else:
            tools = None
            
        # check if this is the first message in the chat
        if self.chat is None:
            self.chat = Chat(user=self.user, db=self.db, configs=self.configs, logger=self.logger)
            self.chat.init_chat(prompt)
        else:
            self.chat.add_message(MessageDocuments(message=Message(role="user", content=prompt)))

        # intial call to the LLM
        try:
            response = self.llm_client.send_request(messages=self.chat.messages, tools=tools)
        except LlmCallFailedError as e:
            return self._fail(f"LLM call failed: {e}")
        response_message = self.llm_client.get_messsage(response=response)
        
        if not response_message.tool_calls:
            self.chat.add_message(MessageDocuments(message=response_message))
            return MessageDocuments(message=response_message)

        return self._run_tool_flow(response_message)
    
########################################
### Methods for the CLI interface.
### Might need work.
########################################

    def cli_get_user_name(self, user_name: str):
        while True:
            try:
                self.user = User(configs=self.configs, db=self.db, user_name=user_name)
                self.chat = Chat(user=self.user, db=self.db, configs=self.configs, logger=self.logger)
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
                self.chat = Chat(user=self.user, db=self.db, configs=self.configs, logger=self.logger)
                self.logger.info(f"Created user {user_name}.")
                return
            except UserAlreadyExistsError as e:
                self.logger.error(f"User already exists: {e}")
                user_name = input("Select a user name>> ")
                continue
    
    # use this to parse prompts from the CLI before calling process_prompt()
    def cli_parse_prompt(self, prompt: str) -> list[Tool] | None :
        if "--" not in prompt:
            return prompt, None
        prompt_list = prompt.split("--")
        prompt = prompt_list.pop(0)

        tool_list = []
        for tool_name in prompt_list:
            tool_name = tool_name.strip()
            if tool_name not in self.tool_client.tool_names:
                self.logger.warning(f"Tool not found: {tool_name}. Skipping.")
            else:
                tool_list.append(self.tool_client.tool_chain[tool_name])
        return prompt, tool_list
    
########################################
### the following are methods for 
### handling LLM responses as a stream
########################################
    def process_prompt_streaming(self, prompt: str):
        prompt, tools = self._parse_prompt(prompt)
        self.chat.add_message(MessageDocuments(message=Message(role="user", content=prompt)))

        content_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        tool_call_flag: bool = False

        try:
            stream = self.llm_client.send_request_stream(messages=self.chat.messages, tools=tools)
            for chunk in stream:
                delta = chunk["choices"][0]["delta"]

                if "content" in delta:
                    token = delta["content"]
                    if token is not None:
                        content_parts.append(token)
                        yield StreamEvent(type="token", content=token)

                if "tool_calls" in delta and delta["tool_calls"] is not None:
                    tool_call_flag = True
                    self.logger.info(f"tool calls in delta: {delta["tool_calls"]}")
                    self._accumulate_tool_calls(tool_calls, delta["tool_calls"])
                    self.logger.info(f"tool_calls after _accumulate_tool_calls: {tool_calls}")

            finish_reason = chunk["choices"][0].get("finish_reason")
            self.logger.info(f"final chunk: {chunk}")

            if tool_call_flag is True:
                response_message = Message(role="assistant", tool_calls=tool_calls)
                yield from self._run_tool_flow_stream(response_message=response_message)
                return
            else:
                final_message = Message(
                        role="assistant",
                        content="".join(content_parts),
                        )
                self.chat.add_message(MessageDocuments(message=final_message))

            yield StreamEvent(type="done")

        except LlmCallFailedError as e:
            self.logger.error(f"Streaming failed: {e}")
            yield StreamEvent(type="error", content=str(e))

    def _accumulate_tool_calls(
            self,
            tool_calls: list[ToolCall],
            delta_tool_calls: list[dict],
        ) -> None:
        """
        Incrementally builds ToolCall objects from streamed tool_call deltas.

        Mutates `tool_calls` in place.
        """

        for call in delta_tool_calls:
            # this is a little tricky because the delta chunks only use the call ID in the first chunk and it's None after that
            # so you have to grab the index of the call and add it to the pydantic model object as "_index" using .setattr()
            # then when you get an existing tool_call object from tool_calls to write the next chunk to, find it by "_index"
            call_id = call["id"]
            call_index = call["index"]

            tool_call = next(
                (tc for tc in tool_calls if getattr(tc, "_index", None) == call_index),
                None
            )

            if tool_call is None:
                tool_call = ToolCall(
                    id=call_id,
                    type="function",
                    function=FunctionCall(
                        name=call["function"].get("name"),
                        arguments=""
                    ),
                )

                setattr(tool_call, "_index", call_index)
                tool_calls.append(tool_call)

            args_fragment = call["function"].get("arguments")
            if args_fragment:
                tool_call.function.arguments += args_fragment

    def _run_tool_flow_stream(self, response_message: Message) -> Iterator[dict]:
        
        # add the model's tool_call message to the chat
        self.chat.add_message(msg_docs=MessageDocuments(message=response_message))

        # call the tool (RAG client), get: 
        #   1) the message to return to the LLM, 
        #   2) the documents returned by the RAG client
        # they will be a list of MessageDocuments objects
        for tool_call in response_message.tool_calls:
            self.logger.info(f"Tool call! name: {tool_call.function.name}, arguments: {tool_call.function.arguments}")
        try:
            tool_responses = self.tool_client.handle(response_message)
        except RagClientFailedError as e:
            return self._fail(f"RAG client failed: {e}")
        
        # TODO: i think there's a problem with the logic here.
        documents = []
        for msg_docs in tool_responses:
            self.logger.info("Tool call added to chat.")
            self.logger.info(f"tool_call_id: {msg_docs.message.tool_call_id}")
            documents.extend(msg_docs.documents)
            self.chat.add_message(msg_docs=msg_docs)

        # send the query with the context gathered from the RAG client
        try:
            stream = self.llm_client.send_request_stream(messages=self.chat.messages)
        except LlmCallFailedError as e:
            return self._fail(f"LLM call failed: {e}")
        
        content_parts: list = []

        for chunk in stream:
            token = chunk["choices"][0]["delta"]["content"]
            if token is not None:
                content_parts.append(token)
            yield StreamEvent(type="token", content=token)

        # then combine the streamed tokens, create the message, and add it to the chat as a MessageDocuments
        # containing the documents/metadata returned by the RAG client.
        final_response_message = Message(
                role="assistant",
                content="".join(content_parts),
            )
        msg_docs = MessageDocuments(message=final_response_message, documents=documents)
        self.chat.add_message(msg_docs=msg_docs)

        # and close the stream.
        yield StreamEvent(type="done")