from app.services.db_manager import DatabaseManager
from app.core.config import Configurations

class UserNotFoundError(Exception):
    """Raised when a user is not found in the database"""
    pass

class User:
    def __init__(self, configs: Configurations, db: DatabaseManager, user_name: str):
        self.configs = configs
        self.db = db
        self.logger = configs.logger
        self.name = user_name
        self.id = self.get_id()

    def get_id(self):
        user_id= self.db.check_user(user_name=self.name)
        if user_id is None:
            self.logger.warning(f"User {self.name} not found in the database.")
            raise UserNotFoundError(f"User {self.name} not found in the database.")
        return user_id

# pattern for instantiating a user:
#             
# try:
#     user = User(configs, db, "john_doe")
# except UserNotFoundError as e:
#     # Handle the missing user case
#     print(f"Error: {e}")