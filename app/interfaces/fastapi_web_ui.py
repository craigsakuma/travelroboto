# Third-party
from fastapi import FastAPI, APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Local application
from app.chatbot.conversation import get_chat_response
from app.schemas.chat import ChatRequest


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application for the web UI.
    """
    app = FastAPI(title="Chatbot Web Interface")

    # Static files & templates
    app.mount(
        "/static",
        StaticFiles(directory="app/interfaces/web/static"),
        name="static"
    )
    templates = Jinja2Templates(directory="app/interfaces/web/templates")

    # Router
    router = APIRouter()

    # @app.get("/", response_class=HTMLResponse)
    @app.get("/", response_class=JSONResponse)
    async def chat_page(request: Request):
        return templates.TemplateResponse("chat.html", {"request": request})

    @router.get("/")
    async def home(request: Request):
        return templates.TemplateResponse("chat.html", {"request": request})

    @router.post("/chat")
    async def chat_endpoint(req: ChatRequest):
        history = get_chat_response(session_id, message)
        # history, _ = get_chat_response(req.message, req.session_id)
        # return {"response": history}
        return JSONResponse(history)


    @router.post("/chat")
    async def chat_endpoint(chat_request: ChatRequest):
        response = get_chat_response(chat_request.message)
        return JSONResponse(content={"response": response})

    app.include_router(router)
    return app
