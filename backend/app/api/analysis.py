
from fastapi import APIRouter, HTTPException

from app.parser.repository_parser import RepositoryParser


router = APIRouter(
    prefix="/api/repositories",
    tags=["Repository Analysis"]
)

repository_parser = RepositoryParser()


@router.post("/{repository_id}/parse")
def parse_repository(repository_id: str):

    try:

        result = repository_parser.parse_repository(
            repository_id
        )

        return {
            "success": True,
            "message": "Repository AST analysis completed.",
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
            detail=f"AST analysis failed: {error}"
        )
