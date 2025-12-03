import sqlite3, time, json
from app.core.config import Configurations
from typing import TYPE_CHECKING
from app.core.errors import *
from app.models import Message, ChromaDbResult

if TYPE_CHECKING:
    from app.services.chat import Chat   # type-checking only, no runtime import

class DatabaseManager:

    def __init__(self, configs: Configurations):
        self.configs = configs
        self.conn = sqlite3.connect(self.configs.sqlite_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._create_users_table()
        self._create_chats_table()
        self._create_messages_table()
    
    def _create_users_table(self):
        """
        creates the users table for the first time
        """
        cursor = self.conn.cursor()
        cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_name TEXT UNIQUE,
            created_at INTEGER
            )
        """)
    
    def _create_chats_table(self):
        """
        creates chats table for the first time 
        """
        cursor = self.conn.cursor()
        cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            created_at INTEGER,
            updated_at INTEGER,
            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
            )
        """
        )

    def _create_messages_table(self):
        """
        creates a table where the messages and associated documents are stored
        """
        cursor = self.conn.cursor()
        cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            message TEXT,
            documents TEXT,
            created_at INTEGER,
            FOREIGN KEY (chat_id)
                REFERENCES chats(id)
                ON DELETE CASCADE
            )
        """
        )
    
        
    def create_user(self, user_name):
        """
        inserts a user into the users table.
        """
        if self.check_user(user_name=user_name):
            raise UserAlreadyExistsError(f"User {user_name} already exists in the database")
        created_at = int(time.time())
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (user_name, created_at)
            VALUES (?, ?)
            """,
            (user_name, created_at)
        )

    def check_user(self, user_name: str):
        """
        verifies user name, returns id
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE user_name = ?
            """,
            (user_name,)
        )

        row = cursor.fetchone()

        # add error handling/logging here
        if row is None:
            return None  # no user with that name

        return row[0]

    
    def create_chat(self, user_id: int, init_message: Message) -> int:
        """
        instantiates a new chat record, returning the chat id.
        """
        created_at = int(time.time())
        cursor = self.conn.cursor()
        cursor.execute(
                """
                INSERT INTO chats (user_id, created_at)
                VALUES (?, ?)
                """,
                (user_id, created_at)
            )
        self.conn.commit()
        chat_id = cursor.lastrowid
        self.insert_message(chat_id=chat_id, message=init_message)
        return chat_id
    

    def insert_message(
            self, 
            chat_id: int, 
            message: Message, 
            documents: list[ChromaDbResult] = None):
        """
        inserts a message and associated documents (if present) into the messages table
        """
        message = json.dumps(message.model_dump())
        if documents:
            documents = json.dumps([document.model_dump() for document in documents])
        time_stamp = int(time.time())
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO messages (chat_id, message, documents, created_at)
            VALUES (?, ?, ?, ?)
            """, (chat_id, message, documents, time_stamp)
        )
        cursor.execute(
            """
            UPDATE chats
            SET updated_at = ?
            WHERE id = ?
            """, (time_stamp, chat_id)
        )
    
    ## replaced by self.insert_message()
    # def save_chat(self, chat: "Chat"):
    #     """
    #     saves an existing chat to the SQLite database
    #     """
    #     updated_at = int(time.time())
    #     messages_blob = chat.dump_to_blob()
    #     cursor = self.conn.cursor()
    #     cursor.execute(
    #         """
    #         UPDATE chats
    #         SET messages = ?, updated_at = ?
    #         WHERE id = ?
    #         """,
    #         (messages_blob, updated_at, chat.chat_id)
    #     )

    #     self.conn.commit()

    def get_messages(self, chat_id: int) -> list[tuple[str, str | None]]:
        """
        gets messages and documents from the SQLite messages table...
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT message, documents
            FROM messages
            WHERE chat_id = ?
            ORDER BY created_at ASC
            """,
            (chat_id,)
        )

        rows = cursor.fetchall()

        # add error handling/logging here
        if not rows:
            return None  # no chat with that ID

        return rows
