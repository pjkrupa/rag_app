import time, json
from rag_app.app.services.db_manager import DatabaseManager


# A helper function to add fake values to an in-memory SQLite database via 
# a DatabaseManager object.

def build_db(fake_db: DatabaseManager, fake_messages):
     ts = int(time.time())
     with fake_db._get_conn() as conn:
            cursor = conn.cursor()

            # generate the fake records
            # user and chat ids will be 1
            cursor.execute(
                """
                INSERT INTO users (user_name, created_at)
                VALUES (?, ?)
                """,
                ("peter", ts)
                )
            user_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO chats (user_id, created_at, updated_at)
                VALUES (?, ?, ?)
                """,
                (user_id, ts, ts)
                )
            chat_id = cursor.lastrowid

            msg_blob = fake_messages.message.model_dump_json()
            docs_blob = json.dumps([d.model_dump() for d in fake_messages.documents])
            
            cursor.execute(
                """
                INSERT INTO messages (chat_id, message, documents, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (chat_id, msg_blob, docs_blob, ts)
                )
            return