from fastapi import FastAPI
from pydantic import BaseModel
from app.models import Message, ChromaDbResult
from app.services.orchestrator import Orchestrator
from app.core.config import set_configs
from app.core.logging_setup import get_logger
class ChatQuery(BaseModel):
    text: str

logger = get_logger()
configs = set_configs(logger=logger)
orchestrator = Orchestrator(configs=configs)
orchestrator.default_user()
app = FastAPI()


@app.post("/chat")
def chat(req: ChatQuery) -> tuple[Message, list[ChromaDbResult] | None]:
    message, documents = orchestrator.process_prompt(req.text)
    print(f"Message: {message}")
    print(f"Documents: {documents}")
    return message, documents