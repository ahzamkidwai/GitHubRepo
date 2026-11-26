from fastapi import APIRouter, HTTPException

from app.chunking.repository_chunker import RepositoryChunker


router = APIRouter(
    prefix="/api/repositories",
    tags=["Repository Chunking"]
)

repository_chunker = RepositoryChunker()


@router.post("/{repository_id}/chunk")
def chunk_repository(repository_id: str):

    try:
        result = repository_chunker.chunk_repository(
            repository_id
        )

        return {
            "success": True,
            "message": "Repository code chunking completed.",
            "result": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Chunking failed: {error}"
        )