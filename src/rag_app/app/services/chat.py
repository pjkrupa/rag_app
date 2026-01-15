import json
from logging import Logger
from rag_app.app.core.config import Configurations
from rag_app.app.core.errors import ChatNotFoundError
from rag_app.app.models import Message, ChromaDbResult, MessageDocuments, UserModel
from rag_app.app.services.db_manager import DatabaseManager
from rag_app.app.services.user import User


class Chat:
    def __init__(
            self, 
            logger: Logger,
            user: UserModel, 
            db: DatabaseManager, 
            configs: Configurations, 
            chat_id: int = None,
            ):
        self.logger = logger
        self.configs = configs
        self.id = chat_id
        self.user = user
        self.db = db
        self.slug = None
        self.messages = [MessageDocuments(message=Message(role="system", content=configs.system_prompt))]
        
        if self.id:
            self._load_messages()
            self._load_slug()

    def init_chat(self, prompt: str):
        """
        run this method for the first prompt in the chat.
        it will save the chat to the database with the system message, set a chat_id,
        and add the user first message to the chat.
        """
        init_message = self.messages[0]
        self.id = self.db.create_chat(user_id=self.user.id, init_message=init_message)
        self.add_message(MessageDocuments(message=Message(role="user", content=prompt)))

    def add_message(self, msg_docs: MessageDocuments):
        message_id = self.db.insert_message(chat_id=self.id, msg_docs=msg_docs)
        msg_docs.id = message_id
        self.messages.append(msg_docs)
        if self.slug is None:
            self.slug = self.create_slug(msg_docs.message.content)
        self.logger.info(f"Message added.")
        self.logger.info(f"role: {msg_docs.message.role}")
        self.logger.info(f"content: {msg_docs.message.content}")
        self.logger.info(f"tool_call_id: {msg_docs.message.tool_call_id}")
        return message_id
    
    def create_slug(self, content: str):
        slug = content[:50] + "..."
        self.db.add_slug(chat_id=self.id, slug=slug)
        self.logger.info(f"Added slug {slug} to chat {self.id}")
        return slug
    
    def dump_to_blob(self) -> str:
        return json.dumps([message.model_dump() for message in self.messages])
    
    def blobs_to_msg_docs(self, messages_docs: list[tuple[str, str | None]]) -> list[MessageDocuments]:
        messages = []
        for message_blob, documents_blob in messages_docs:
            msg_docs = MessageDocuments.model_validate({
            "message": json.loads(message_blob),
            "documents": json.loads(documents_blob) if documents_blob else None
            })
            messages.append(msg_docs)
        return messages

    def _load_messages(self):
        messages_docs = self.db.get_messages(chat_id=self.id)
        if messages_docs is None:
            self.logger.warning(f"Chat {self.id} not found in the database.")
            raise ChatNotFoundError(f"Chat {self.id} not found in the database.")
        self.messages = self.blobs_to_msg_docs(messages_docs=messages_docs)

    def _load_slug(self):
        self.slug = self.db.get_slug(chat_id=self.id)