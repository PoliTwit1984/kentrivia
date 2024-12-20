from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "main/index.html",
        {"request": request}
    )

@router.get("/how-to-play", response_class=HTMLResponse)
async def how_to_play(request: Request):
    return templates.TemplateResponse(
        "main/how_to_play.html",
        {"request": request}
    )
