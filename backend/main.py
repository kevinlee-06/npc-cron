from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from database import engine, Base
import models
import os
from routers import assets, schedules, system
from scheduler import run_scheduler

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_scheduler())
    yield
    task.cancel()

app = FastAPI(title="沒空 API", lifespan=lifespan)

app.include_router(assets.router)
app.include_router(schedules.router)
app.include_router(system.router)

# Backend API routes can be mounted here under /api
@app.get("/api/status")
def read_root():
    return {"status": "ok", "message": "沒空 API is running"}

# Static Files for pure HTML/CSS/JS frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/{catchall:path}")
def serve_frontend(catchall: str):
    # Serve index.html as a single-page app
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend not found"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
