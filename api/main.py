import markdown
from functools import lru_cache
from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.models import Message, ChromaDbResult
from app.services.orchestrator import Orchestrator
from app.core.config import set_configs
from app.core.logging_setup import get_logger
from api.session_manager import SessionManager


templates = Jinja2Templates(directory="./frontend/templates/")
templates.env.filters["markdown"] = lambda text: markdown.markdown(
    text,
    extensions=["fenced_code", "tables"]
)
@lru_cache
def get_session_manager():
    return SessionManager()

logger = get_logger()
configs = set_configs(logger=logger)
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def get_chat(
    request: Request,
    sm: SessionManager = Depends(get_session_manager)
    ):
    session = Orchestrator(configs=configs)
    session.default_user()
    chat_id = session.chat.chat_id
    sm.sessions[chat_id] = session
    logger.debug(f"chat_id_1: {chat_id}")
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "chat_id": chat_id,
        }
    )

@app.post("/chat", response_class=HTMLResponse)
async def post_chat(
    request: Request, 
    prompt: str = Form(...),
    chat_id: int | None = Form(default=None),
    sm: SessionManager = Depends(get_session_manager)
        ):    
    session = sm.sessions.get(chat_id)
    if session is None:
        return HTMLResponse("Session expired or invalid", status_code=400)
    logger.debug(f"chat_id_4: {chat_id}")
    message, documents = session.process_prompt(prompt=prompt)
    return templates.TemplateResponse("chat-box.html", {
        "request": request,
        "messages": session.chat.messages,
        "chat_id": chat_id,
        }
    )