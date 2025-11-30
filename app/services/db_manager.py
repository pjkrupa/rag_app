import sqlite3
from uuid import uuid4
from app.core.config import Configurations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.chat import Chat   # type-checking only, no runtime import

class DatabaseManager:

    def __init__(self, configs: Configurations):
        self.configs = configs
        self.conn = sqlite3.connect(self.configs.sqlite_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._create_users_table()
        self._create_chats_table()
    
    def _create_users_table(self):
        """
        creates the users table for the first time
        """
        cursor = self.conn.cursor()
        cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            user_name TEXT
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
            user_id TEXT,
            messages TEXT,
            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
            )
        """)
    
    def create_user(self, user_name):
        """
        inserts a user into the users table.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (id, user_name)
            VALUES (?, ?)
            """,
            (uuid4(), user_name)
        )

    def create_chat(self, user_id: str, messages_blob: str) -> int:
        """
        instantiates a new chat record, returning the chat id.
        """
        cursor = self.conn.cursor()
        cursor.execute(
                """
                INSERT INTO chats (user_id, messages)
                VALUES (?, ?)
                """,
                (user_id, messages_blob)
            )
        self.conn.commit()
        return cursor.lastrowid
    
    def save_chat(self, chat: "Chat") -> int:
        """
        saves an existing chat to the SQLite database
        """
        messages_blob = chat.dump_to_blob()
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE chats
            SET messages = ?
            WHERE id = ?
            """,
            (messages_blob, chat.id)
        )

        self.conn.commit()

    def get_messages(self, chat_id: int) -> str:
        """
        gets messages from the SQLite chats table... returns them as a JSON blob
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT messages
            FROM chats
            WHERE id = ?
            """,
            (chat_id,)
        )

        row = cursor.fetchone()

        # add error handling/logging here
        if row is None:
            return None  # no chat with that ID

        return row[0]
