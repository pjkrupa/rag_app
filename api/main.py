import markdown, html, asyncio
from typing import AsyncGenerator
from functools import lru_cache
from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.models import Message, ChromaDbResult, MessageDocuments
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
    session.logger.info(f"chat_id in GET: {chat_id}")
    sm.sessions[chat_id] = session
    session.logger.info(f"Sessions logged by session manager: {sm.sessions.keys()}")
    
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
    msg_docs = session.process_prompt(prompt=prompt)
    
    return templates.TemplateResponse("chat-box.html", {
        "request": request,
        "user_message": user_message,
        "llm_message": msg_docs.message,
        "documents": msg_docs.documents,
        "chat_id": chat_id,
        }
    )

############
# streaming endpoints (doesn't work)
############

# @app.post("/chat/start", response_class=HTMLResponse)
# async def post_chat(
#     request: Request, 
#     prompt: str = Form(...),
#     chat_id: int | None = Form(default=None),
#     sm: SessionManager = Depends(get_session_manager)
#         ):
#     session = sm.sessions.get(chat_id)
#     if session is None:
#         return HTMLResponse("Session expired or invalid", status_code=400)
#     user_message = MessageDocuments(message=Message(role="user", content=prompt))
#     message_id = session.chat.add_message(user_message)
    
#     return templates.TemplateResponse("chat-stream.html", {
#         "request": request,
#         "prompt": prompt,
#         "message_id": message_id,
#         "chat_id": chat_id,
#         }
#     )

# this doesn't work yet, might never work. leaving for later.
# @app.get("/chat/stream/{chat_id}/{message_id}")
# async def get_chat_stream(
#     request: Request,
#     message_id: int,
#     chat_id: int,
#     sm: SessionManager = Depends(get_session_manager),
# ):
#     session = sm.sessions.get(chat_id)
#     prompt = next(msg.message.content for msg in session.chat.messages if msg.id == message_id)

#     async def event_stream() -> AsyncGenerator[str, None]:

#         # assistant message start
#         yield (
#             "event: assistant_start\n"
#             "data: \n\n"
#         )

#         try:
#             prev_ended_space = False

#             for event in session.process_prompt_streaming(prompt):
#                 if await request.is_disconnected():
#                     break

#                 if event.type == "token":
#                     text = event.content + " "
#                     # if text and not text[0].isspace() and not prev_ended_space:
#                     #     text = " " + text
#                     #     prev_ended_space = text[-1].isspace()

#                     yield (
#                         "event: token\n"
#                         f"data: {html.escape(text)}\n\n"
#                     )

#                 elif event.type == "error":
#                     yield (
#                         "event: error\n"
#                         f"data: {html.escape(event.content)}\n\n"
#                     )
#                     return

#                 elif event.type == "done":
#                     break

#         finally:
#             yield (
#                 "event: assistant_end\n"
#                 "data: \n\n"
#             )

#     return StreamingResponse(
#         event_stream(),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "X-Accel-Buffering": "no",  # critical for nginx
#         },
#     )