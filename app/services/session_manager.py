from core.config import Configurations
from services.db_manager import DatabaseManager
from services.chat import Chat
from models import Message

class SessionManager:
    def __init__(self, configs: Configurations, user_id: str, chat_id: int = None):
        self.configs = configs
        self.user_id = user_id
        self.db = DatabaseManager(configs=self.configs)
        self.chat = Chat(db=self.db, user_id=user_id, configs=configs, chat_id=chat_id)
        
    
    