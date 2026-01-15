from dataclasses import dataclass
from fastapi import APIRouter, Form, Request, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from rag_app.app.models import Message
from rag_app.app.services.session import Session
from rag_app.app.core.config import Configurations
from rag_app.app.core.errors import UserAlreadyExistsError
from rag_app.api.deps import get_session_manager, SessionManager

# model and helper function for getting objects from app state
@dataclass(frozen=True)
class AppState:
    templates: Jinja2Templates
    configs: Configurations

def get_state(request:Request) -> AppState:
    return AppState(
        templates=request.app.state.templates,
        configs=request.app.state.configs
    )

def get_root_path(request: Request) -> str:
    return request.scope.get("root_path", "")

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def main_page(
    request: Request,
    flash_error: str | None = Cookie(default=None),
    session_id: str | None = Cookie(default=None),
    sm: SessionManager = Depends(get_session_manager)
):
    print("cookie:", session_id)
    print("sessions:", [session.id for session in sm.sessions])
    
    app = get_state(request=request)

    root_path = get_root_path(request=request)

    invalid = not session_id or not sm.has_session(session_id)

    if invalid:
        session = Session(configs=app.configs)

        sm.sessions.append(session)
        
    else:
        session = sm.get_session(session_id)

    users = [row[1] for row in session.db.get_users()]

    response = app.templates.TemplateResponse(
        "main.html",
        {"request": request, "users": users, "error": flash_error,},
    )

    if flash_error:
        response.delete_cookie("flash_error", path=root_path)

    if invalid:
        response.set_cookie(
            key="session_id",
            value=session.id,
            httponly=True,
            secure=False,
            samesite="lax",
            path=root_path,
        )

    return response


@router.get("/users/{user_name}", name="user_page")
async def get_user(
    request: Request,
    user_name: str,
    session_id: str | None = Cookie(default=None),
    sm: SessionManager = Depends(get_session_manager)
):
    app = get_state(request=request)
    root_path = get_root_path(request=request)
    print("cookie:", session_id)
    print("sessions:", [session.id for session in sm.sessions])
    if not session_id or not sm.has_session(session_id):
        redirect = RedirectResponse(f"{root_path}/", status_code=303)
        return redirect

    session = sm.get_session(session_id=session_id)

    # clears the chat from the session 
    session.chat = None

    session.load_user(user_name=user_name)
    chats = session.user.get_chats()

    return app.templates.TemplateResponse(
        "main.html", 
        {"request": request, "chats": chats, "user_name": user_name},
    )


@router.get("/user/{user_name}/chat/{chat_id}", name="individual_chat", response_class=HTMLResponse)
async def get_chat(
    user_name: str,
    chat_id: str,
    request: Request,
    sm: SessionManager = Depends(get_session_manager),
    flash_error: str | None = Cookie(default=None),
    session_id: str | None = Cookie(default=None),
):
    app = get_state(request=request)
    if not session_id or not sm.has_session(session_id):
        root_path = get_root_path(request=request)
        redirect = RedirectResponse(f"{root_path}/", status_code=303)
        return redirect

    session = sm.get_session(session_id=session_id)
    session.load_chat(chat_id=chat_id)
    chats = session.user.get_chats()

    response = app.templates.TemplateResponse(
        "main.html",
        {"request": request, "chat": session.chat.messages, "user_name": user_name, "chats": chats}
    )
    return response


@router.post("/chat", response_class=HTMLResponse, name="chat")
async def post_chat(
    request: Request, 
    prompt: str = Form(...),
    tool_names: list[str] = Form([]),
    session_id: str | None = Cookie(default=None),
    chat_id: int | None = Form(default=None),
    sm: SessionManager = Depends(get_session_manager)
):
    app = get_state(request=request)
    session = sm.get_session(session_id=session_id)

    print("cookie:", session_id)
    print("sessions:", [session.id for session in sm.sessions])

    if session is None:
        return HTMLResponse("Session expired or invalid", status_code=400)
    app.configs.logger.debug(f"chat_id_4: {chat_id}")
    user_message = Message(role="user", content=prompt)
    msg_docs = session.process_prompt(prompt=prompt, tool_names=tool_names)
    
    return app.templates.TemplateResponse("chat-box.html", {
        "request": request,
        "user_message": user_message,
        "assistant_message": msg_docs.message,
        "documents": msg_docs.documents,
        "chat_id": chat_id,
        }
    )

@router.post("/create_user/", name="create_user")
async def create_user(
    request: Request,
    user_name: str = Form(...),
    session_id: str | None = Cookie(default=None),
    sm: SessionManager = Depends(get_session_manager),
):
    app = get_state(request=request)
    try:
        if not session_id or not sm.has_session(session_id):
            root_path = get_root_path(request=request)
            app.configs.logger.error(f"Session ID not found, redirecting back to main page...")
            return RedirectResponse(f"{root_path}/", status_code=303)
        session = sm.get_session(session_id)
        session.db.create_user(user_name=user_name)
        session.load_user(user_name=user_name)
    except UserAlreadyExistsError as e:
        app.configs.logger.error(f"There was an error creating the user: {e}")
        root_path = get_root_path(request=request)
        redirect = RedirectResponse(f"{root_path}/", status_code=303)
        root_path = get_root_path(request=request)
        redirect.set_cookie(
            "flash_error",
            "User already exists. Please choose another name.",
            max_age=5,
            path=root_path,
        )
        return redirect

    
    url = request.url_for("user_page", user_name=user_name)
    return RedirectResponse(url, status_code=303)

### old stuff

# @app.get("/", response_class=HTMLResponse)
# async def get_chat(
#     request: Request,
#     sm: SessionManager = Depends(get_session_manager)
#     ):
#     session = Session(configs=configs)

#     # This is just for dev. maybe move it to a config.
#     session.default_user()

#     chat_id = session.chat.id
#     session.logger.info(f"chat_id in GET: {chat_id}")
#     sm.sessions[chat_id] = session
#     session.logger.info(f"Sessions logged by session manager: {sm.sessions.keys()}")
    
#     return templates.TemplateResponse("chat.html", {
#         "request": request,
#         "user_message": None,
#         "assistant_message": None,
#         "chat_id": chat_id,
#         }
#     )



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