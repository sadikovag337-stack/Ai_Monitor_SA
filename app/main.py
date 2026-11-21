from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.db.database import init_db
from app.services.stream_manager import manager
from app.api.routes import router

BASE = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app):
    init_db()
    manager.sync()
    yield
    manager.stop_all()

app = FastAPI(title="AI MONITOR", lifespan=lifespan)
app.include_router(router, prefix="/api")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "templates/index.html").read_text(encoding="utf-8")
