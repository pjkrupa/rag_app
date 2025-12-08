import markdown
from functools import lru_cache
from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.models import Message, ChromaDbResult
from app.services.orchestrator import Orchestrator
from app.core.config import Configurations
from app.core.errors import ConfigurationsError
from app.core.logging_setup import get_logger
from api.session_manager import SessionManager


templates = Jinja2Templates(directory="./frontend/templates/")
templates.env.filters["markdown"] = lambda text: markdown.markdown(
    text,
    extensions=["fenced_code", "tables"]
)

# sets up the SessionManager object to be loaded into FastAPI as a dependency 
@lru_cache
def get_session_manager():
    return SessionManager()

logger = get_logger()

# instantiates the configurations by fetching them from a YAML file
# and logging any problems
try:
    configs = Configurations.load(logger=logger)
except ConfigurationsError as e:
    logger.error(f"The configurations didn't load correctly: {e}")

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def get_chat(
    request: Request,
    sm: SessionManager = Depends(get_session_manager)
    ):
    session = Orchestrator(configs=configs)

    # This is just for dev. maybe move it to a config.
    session.default_user()

    chat_id = session.chat.chat_id
    sm.sessions[chat_id] = session
    
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "user_message": None,
        "llm_message": None,
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
    user_message = Message(role="user", content=prompt)
    llm_message, documents = session.process_prompt(prompt=prompt)
    
    return templates.TemplateResponse("chat-box.html", {
        "request": request,
        "user_message": user_message,
        "llm_message": llm_message,
        "documents": documents,
        "chat_id": chat_id,
        }
    )