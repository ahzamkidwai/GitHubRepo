
from fastapi import FastAPI

from app.config import APP_NAME
from app.api.repositories import router as repository_router


app = FastAPI(
    title=APP_NAME,
    description=(
        "AI-powered repository intelligence "
        "and codebase understanding system."
    ),
    version="0.1.0"
)


# Register API routes
app.include_router(repository_router)


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
