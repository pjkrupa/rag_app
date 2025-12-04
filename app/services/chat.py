import json
from app.core.config import Configurations
from app.core.errors import ChatNotFoundError
from app.models import Message, ChromaDbResult, MessageDocuments
from app.services.db_manager import DatabaseManager
from app.services.user import User

class Chat:
    def __init__(self, user: User, db: DatabaseManager, configs: Configurations, chat_id: int = None):
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

    def add_message(self, message: Message, documents:ChromaDbResult = None):
        msg_docs = MessageDocuments(message=message, documents=documents)
        self.messages.append(msg_docs)
        self.db.insert_message(chat_id=self.chat_id, msg_docs=msg_docs)
    
    def dump_to_blob(self) -> str:
        return json.dumps([message.model_dump() for message in self.messages])
    
    def blobs_to_messages(self, messages_docs: list[tuple[str, str | None]]):
        messages = []
        for blob, _ in messages_docs:
            messages.append(Message(**json.loads(blob)))
        return messages

    def _load_messages(self):
        messages_docs = self.db.get_messages(chat_id=self.chat_id)
        if messages_docs is None:
            self.logger.warning(f"Chat {self.chat_id} not found in the database.")
            raise ChatNotFoundError(f"Chat {self.chat_id} not found in the database.")
        self.messages = self.blobs_to_messages(messages_docs=messages_docs)