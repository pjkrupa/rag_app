import sqlite3
import time
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
            messages TEXT,
            created_at INTEGER,
            updated_at INTEGER,
            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
            )
        """)
    
    def create_user(self, user_name):
        """
        inserts a user into the users table.
        """
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

    def create_chat(self, user_id: int, messages_blob: str) -> int:
        """
        instantiates a new chat record, returning the chat id.
        """
        created_at = int(time.time())
        cursor = self.conn.cursor()
        cursor.execute(
                """
                INSERT INTO chats (user_id, messages, created_at)
                VALUES (?, ?, ?)
                """,
                (user_id, messages_blob, created_at)
            )
        self.conn.commit()
        return cursor.lastrowid
    
    def save_chat(self, chat: "Chat"):
        """
        saves an existing chat to the SQLite database
        """
        updated_at = int(time.time())
        messages_blob = chat.dump_to_blob()
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE chats
            SET messages = ?, updated_at = ?
            WHERE id = ?
            """,
            (messages_blob, updated_at, chat.chat_id)
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
