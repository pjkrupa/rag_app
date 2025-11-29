import
from core.config import Configurations
from services.db_manager import DatabaseManager
from services.chat import Chat
from models import Message

class SessionManager:
    def __init__(self, configs: Configurations, user_id: str, chat_id: int = None):
        self.configs = configs
        self.user_id = user_id
        self.chat = self._get_chat(chat_id)
        self.db = DatabaseManager(configs=self.configs)
    
    def _get_chat(self, chat_id):
        return Chat(user_id=self.user_id, configs=self.configs, chat_id=chat_id)

        
        
    
    