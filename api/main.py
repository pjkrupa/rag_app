import markdown
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.models import Message, ChromaDbResult
from app.services.orchestrator import Orchestrator
from app.core.config import set_configs
from app.core.logging_setup import get_logger

SESSIONS: dict[int, Orchestrator] = {}

templates = Jinja2Templates(directory="./frontend/templates/")
templates.env.filters["markdown"] = lambda text: markdown.markdown(
    text,
    extensions=["fenced_code", "tables"]
)

logger = get_logger()
configs = set_configs(logger=logger)
app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def get_chat(request: Request):
    return templates.TemplateResponse("chat.html", {
        "request": request,
        }
    )

@app.post("/chat", response_class=HTMLResponse)
async def post_chat(
    request: Request, 
    prompt: str = Form(...),
    chat_id: int | None = Form(default=None),
        ):
    logger.debug(f"chat_id_1: {chat_id}")
    if not chat_id:
        session = Orchestrator(configs=configs)
        session.default_user()
        chat_id = session.chat.chat_id
        SESSIONS[chat_id] = session
        logger.debug(f"chat_id_2: {chat_id}")
    else:
        logger.debug(f"chat_id_3: {chat_id}")
        session = SESSIONS.get(chat_id)
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