from typing import Dict
from rag_app.app.services.session import Session

# build this out later into a robust session manager:
#   - create, get, delete, exists, cleanup_expired

class SessionManager:
    def __init__(self):
        self.sessions: list[Session] = []
    
    def has_session(self, session_id: str) -> bool:
        return any(session.id == session_id for session in self.sessions)
    
    def get_session(self, session_id: str) -> Session | None:
        return next(
            (session for session in self.sessions if session.id == session_id),
            None,
        )

