
import json
import shutil
import uuid

from pathlib import Path

from app.config import REPOSITORY_STORAGE_PATH
from app.ingestion.github_loader import GitHubLoader
from app.ingestion.file_filter import FileFilter


class RepositoryManager:

    def __init__(self):

        self.github_loader = GitHubLoader()
        self.file_filter = FileFilter()

    def ingest_repository(
        self,
        repository_url: str,
        branch: str | None = None
    ):

        repository_id = str(uuid.uuid4())

        repository_path = (
            REPOSITORY_STORAGE_PATH / repository_id
        )

        try:

            # Step 1: Clone repository
            clone_info = self.github_loader.clone_repository(
                repository_url=repository_url,
                destination=repository_path,
                branch=branch
            )

            # Step 2: Scan repository files
            scan_result = self.file_filter.scan_repository(
                repository_path
            )

            # Step 3: Generate repository metadata
            metadata = {
                "repository_id": repository_id,
                "repository_name": clone_info["repository"],
                "repository_owner": clone_info["owner"],
                "repository_url": clone_info["url"],
                "branch": branch,
                "commit_hash": clone_info["commit_hash"],
                "local_path": str(repository_path),
                "total_files": scan_result["total_files"],
                "total_size_bytes": scan_result["total_size_bytes"],
                "skipped_files": scan_result["skipped_files"],
                "truncated": scan_result["truncated"],
                "files": scan_result["files"],
                "status": "ingested"
            }

            # Step 4: Save metadata
            metadata_path = (
                repository_path / "repository_manifest.json"
            )

            with open(
                metadata_path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    metadata,
                    file,
                    indent=4
                )

            return metadata

        except Exception:

            # Clean up incomplete ingestion
            if repository_path.exists():
                shutil.rmtree(repository_path)

            raise
