from functools import lru_cache
from fastapi import Request
from rag_app.app.services.session import Session
from rag_app.api.session_manager import SessionManager

# build this out later into a robust session manager:
#   - create, get, delete, exists, cleanup_expired

@lru_cache
def get_session_manager() -> SessionManager:
    return SessionManager()