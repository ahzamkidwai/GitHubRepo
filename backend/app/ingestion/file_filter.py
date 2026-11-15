
from pathlib import Path

from app.config import (
    MAX_FILE_SIZE_BYTES,
    MAX_REPOSITORY_SIZE_BYTES,
    MAX_REPOSITORY_FILES
)


class FileFilter:

    # Directories to ignore
    IGNORED_DIRECTORIES = {
        ".git",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".next",
        ".nuxt",
        "dist",
        "build",
        "target",
        "coverage",
        "vendor",
        "site-packages"
    }

    # Files that should never be indexed
    IGNORED_FILES = {
        ".env",
        ".env.local",
        ".env.production",
        "id_rsa",
        "id_ed25519"
    }

    # Supported source code extensions
    SUPPORTED_EXTENSIONS = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".go",
        ".rs",
        ".cs",
        ".rb",
        ".php",
        ".swift",
        ".kt"
    }

    def scan_repository(self, repository_path: Path):

        repository_path = Path(repository_path).resolve()

        files = []
        total_size = 0
        skipped_files = 0
        truncated = False

        for file_path in repository_path.rglob("*"):

            if file_path.is_symlink():
                skipped_files += 1
                continue

            if not file_path.is_file():
                continue

            relative_path = file_path.relative_to(
                repository_path
            )

            # Ignore unwanted directories
            if any(
                part in self.IGNORED_DIRECTORIES
                for part in relative_path.parts
            ):
                skipped_files += 1
                continue

            # Ignore hidden and sensitive files
            if (
                file_path.name in self.IGNORED_FILES
                or file_path.name.startswith(".env")
                or file_path.name.endswith((".pem", ".key"))
            ):
                skipped_files += 1
                continue

            # Only process supported extensions
            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                skipped_files += 1
                continue

            file_size = file_path.stat().st_size

            # Skip oversized files
            if file_size > MAX_FILE_SIZE_BYTES:
                skipped_files += 1
                continue

            # Enforce total repository size limit
            if total_size + file_size > MAX_REPOSITORY_SIZE_BYTES:
                truncated = True
                break

            # Enforce maximum file count
            if len(files) >= MAX_REPOSITORY_FILES:
                truncated = True
                break

            files.append({
                "file_path": relative_path.as_posix(),
                "absolute_path": str(file_path),
                "extension": file_path.suffix.lower(),
                "size": file_size
            })

            total_size += file_size

        return {
            "files": files,
            "total_files": len(files),
            "total_size_bytes": total_size,
            "skipped_files": skipped_files,
            "truncated": truncated
        }
