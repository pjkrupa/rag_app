import json
from logging import Logger
from app.core.config import Configurations
from app.core.errors import ChatNotFoundError
from app.models import Message, ChromaDbResult, MessageDocuments
from app.services.db_manager import DatabaseManager
from app.services.user import User


class Chat:
    def __init__(
            self, 
            logger: Logger,
            user: User, 
            db: DatabaseManager, 
            configs: Configurations, 
            chat_id: int = None,
            ):
        self.logger = logger
        self.configs = configs
        self.chat_id = chat_id
        self.user = user
        self.db = db
        self.messages = [MessageDocuments(message=Message(role="system", content=configs.system_prompt))]
        
        if self.chat_id:
            self._load_messages()
        else:
            init_message = self.messages[0]
            self.chat_id = self.db.create_chat(user_id=self.user.id, init_message=init_message)

    def add_message(self, msg_docs: MessageDocuments):
        self.messages.append(msg_docs)
        self.logger.info(f"Message added.")
        self.logger.info(f"role: {msg_docs.message.role}")
        self.logger.info(f"content: {msg_docs.message.content}")
        self.logger.info(f"tool_call_id: {msg_docs.message.tool_call_id}")
        self.db.insert_message(chat_id=self.chat_id, msg_docs=msg_docs)
    
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
        messages_docs = self.db.get_messages(chat_id=self.chat_id)
        if messages_docs is None:
            self.logger.warning(f"Chat {self.chat_id} not found in the database.")
            raise ChatNotFoundError(f"Chat {self.chat_id} not found in the database.")
        self.messages = self.blobs_to_msg_docs(messages_docs=messages_docs)