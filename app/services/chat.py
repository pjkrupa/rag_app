from app.core.config import Configurations
from app.models import Message

class Chat:
    def __init__(self, configs: Configurations, id: str = ""):
        self.configs = configs
        self.id = id
        self.messages = [Message(role="system", content=configs.system_prompt)]
    
    def add_message(self, message: Message):
        self.messages.append(message)