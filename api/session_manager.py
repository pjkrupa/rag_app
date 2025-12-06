from typing import Dict
from app.services.orchestrator import Orchestrator

# build this out later into a robust session manager:
#   - create, get, delete, exists, cleanup_expired

class SessionManager:
    def __init__(self):
        self.sessions: Dict[int, Orchestrator] = {}
