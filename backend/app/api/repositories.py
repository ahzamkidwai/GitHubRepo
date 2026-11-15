
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.ingestion.repository_manager import RepositoryManager


router = APIRouter(
    prefix="/api/repositories",
    tags=["Repositories"]
)

repository_manager = RepositoryManager()


class RepositoryRequest(BaseModel):

    repository_url: HttpUrl
    branch: str | None = None


@router.post("/ingest")
def ingest_repository(request: RepositoryRequest):

    try:

        result = repository_manager.ingest_repository(
            repository_url=str(request.repository_url),
            branch=request.branch
        )

        return {
            "success": True,
            "message": "Repository ingested successfully.",
            "repository": {
                "repository_id": result["repository_id"],
                "repository_name": result["repository_name"],
                "repository_owner": result["repository_owner"],
                "commit_hash": result["commit_hash"],
                "total_files": result["total_files"],
                "total_size_bytes": result["total_size_bytes"],
                "status": result["status"]
            }
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except FileExistsError as error:

        raise HTTPException(
            status_code=409,
            detail=str(error)
        )

    except RuntimeError as error:

        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Repository ingestion failed: {error}"
        )
