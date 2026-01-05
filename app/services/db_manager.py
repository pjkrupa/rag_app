import sqlite3, time, json
from app.core.config import Configurations
from typing import TYPE_CHECKING
from app.core.errors import *
from app.models import MessageDocuments

if TYPE_CHECKING:
    from app.services.chat import Chat   # type-checking only, no runtime import

class DatabaseManager:

    def __init__(self, configs: Configurations):
        self.configs = configs
        self._init_db()
    
    def _init_db(self):
        """ Run DB setup once, using a temporary connection """
        with self._get_conn() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            self._create_users_table(conn)
            self._create_chats_table(conn)
            self._create_messages_table(conn)

    def _get_conn(self):
        return sqlite3.connect(self.configs.sqlite_path, check_same_thread=False, uri=True)

    def _create_users_table(self, conn):
        """
        creates the users table for the first time
        """
        cursor = conn.cursor()
        cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_name TEXT UNIQUE,
            created_at INTEGER
            )
        """)
    
    def _create_chats_table(self, conn):
        """
        creates chats table for the first time 
        """
        cursor = conn.cursor()
        cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            slug TEXT,
            created_at INTEGER,
            updated_at INTEGER,
            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
            )
        """
        )

    def _create_messages_table(self, conn):
        """
        creates a table where the messages and associated documents are stored
        """
        cursor = conn.cursor()
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


    #---------------------#
    ### CRUD operations ###
    #---------------------#

    def create_user(self, user_name):
        """
        inserts a user into the users table.
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()

            if self.check_user(user_name=user_name):
                raise UserAlreadyExistsError(f"User {user_name} already exists in the database")
            created_at = int(time.time())
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
        with self._get_conn() as conn:
            cursor = conn.cursor()
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

    
    def create_chat(self, user_id: int, init_message: MessageDocuments) -> int:
        """
        instantiates a new chat record, returning the chat id.
        """
        created_at = int(time.time())
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                    """
                    INSERT INTO chats (user_id, created_at)
                    VALUES (?, ?)
                    """,
                    (user_id, created_at)
                )
            conn.commit()
            chat_id = cursor.lastrowid
        self.insert_message(chat_id=chat_id, msg_docs=init_message)
        return chat_id
    
    def add_slug(self, chat_id: int, slug: str):
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE chats
                SET slug = ?
                WHERE id = ?
                """, (slug, chat_id,)
            )

    
    def update_message(
            self,
            message_id: int,
            chat_id: int,
            msg_docs: MessageDocuments
    ):
        message = json.dumps(msg_docs.message.model_dump())
        if msg_docs.documents:
            documents = json.dumps([document.model_dump() for document in msg_docs.documents])
        else:
            documents = None
        time_stamp = int(time.time())
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (chat_id, message, documents)
                VALUES (?, ?, ?)
                WHERE id = ?
                """, (chat_id, message, documents, message_id)
            )

            message_id = cursor.lastrowid

            cursor.execute(
                """
                UPDATE chats
                SET updated_at = ?
                WHERE id = ?
                """, (time_stamp, chat_id)
            )
            conn.commit()

    def insert_message(
            self, 
            chat_id: int, 
            msg_docs: MessageDocuments):
        """
        inserts a message and associated documents (if present) into the messages table
        """
        message = json.dumps(msg_docs.message.model_dump())
        if msg_docs.documents:
            documents = json.dumps([document.model_dump() for document in msg_docs.documents])
        else:
            documents = None
        time_stamp = int(time.time())
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (chat_id, message, documents, created_at)
                VALUES (?, ?, ?, ?)
                """, (chat_id, message, documents, time_stamp)
            )

            message_id = cursor.lastrowid

            cursor.execute(
                """
                UPDATE chats
                SET updated_at = ?
                WHERE id = ?
                """, (time_stamp, chat_id)
            )
            conn.commit()
            
            return message_id

    #---------------------#
    ### query operations ###
    #---------------------#

    def get_users(self) -> list[tuple[int, str]]:
        """
        Gets all the users from the database and returns them as a list of User objects
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_name
                FROM users
                """,
            )
            rows = cursor.fetchall()
            return rows

    def get_messages(self, chat_id: int) -> list[tuple[str, str | None]]:
        """
        gets messages and documents from the SQLite messages table...
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
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
    
    def get_chats(self, user_id: int) -> list[tuple[int, str]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, slug
                FROM chats
                WHERE user_id = ?
                ORDER BY created_at ASC
                LIMIT 10 
                """,
                (user_id,)
            )

            return cursor.fetchall()
