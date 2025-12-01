import json
from app.core.config import Configurations
from app.models import Message
from app.services.db_manager import DatabaseManager
from app.services.user import User


class ChatNotFoundError(Exception):
    """Raised when a chat is not found in the database"""
    pass

class Chat:
    def __init__(self, user: User, db: DatabaseManager, configs: Configurations, chat_id: int = None):
        self.configs = configs
        self.chat_id = chat_id
        self.user = user
        self.db = db
        self.messages = [Message(role="system", content=configs.system_prompt)]
    
        if self.chat_id:
            self._load_messages()
        else:
            messages_blob = self.dump_to_blob()
            self.chat_id = self.db.create_chat(user_id=self.user.id, messages_blob=messages_blob)

    def add_message(self, message: Message):
        self.messages.append(message)
        self.db.save_chat(self)
    
    def dump_to_blob(self) -> str:
        return json.dumps([message.model_dump() for message in self.messages])
    
    def blob_to_messages(self, messages_blob: str):
        return [Message(**obj) for obj in json.loads(messages_blob)]

    def _load_messages(self):
        messages_blob = self.db.get_messages(chat_id=self.chat_id)
        if messages_blob is None:
            self.logger.warning(f"Chat {self.chat_id} not found in the database.")
            raise ChatNotFoundError(f"Chat {self.chat_id} not found in the database.")
        self.messages = self.blob_to_messages(messages_blob=messages_blob)