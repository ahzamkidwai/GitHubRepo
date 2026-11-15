
from fastapi import FastAPI

from app.config import APP_NAME

from app.api.repositories import (
    router as repository_router
)

from app.api.analysis import (
    router as analysis_router
)


app = FastAPI(
    title=APP_NAME,
    description="AI-powered repository intelligence system.",
    version="0.2.0"
)


app.include_router(repository_router)
app.include_router(analysis_router)


@app.get("/")
def root():

    return {
        "message": "Welcome to RepoMind",
        "status": "running"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }
