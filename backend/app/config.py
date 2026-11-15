
import os
from pathlib import Path

from dotenv import load_dotenv

# Backend root directory
BASE_DIR = Path(__file__).resolve().parents[1]

# Load environment variables
load_dotenv(BASE_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "RepoMind")
APP_ENV = os.getenv("APP_ENV", "development")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Repository storage
REPOSITORY_STORAGE_PATH = Path(
    os.getenv(
        "REPOSITORY_STORAGE_PATH",
        "data/repositories"
    )
)

if not REPOSITORY_STORAGE_PATH.is_absolute():
    REPOSITORY_STORAGE_PATH = (
        BASE_DIR / REPOSITORY_STORAGE_PATH
    )

REPOSITORY_STORAGE_PATH.mkdir(
    parents=True,
    exist_ok=True
)

# Repository ingestion limits
MAX_REPOSITORY_FILES = int(
    os.getenv("MAX_REPOSITORY_FILES", "5000")
)

MAX_FILE_SIZE_MB = int(
    os.getenv("MAX_FILE_SIZE_MB", "1")
)

MAX_REPOSITORY_SIZE_MB = int(
    os.getenv("MAX_REPOSITORY_SIZE_MB", "200")
)

MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

MAX_REPOSITORY_SIZE_BYTES = (
    MAX_REPOSITORY_SIZE_MB * 1024 * 1024
)
