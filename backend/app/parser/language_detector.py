
from pathlib import Path


class LanguageDetector:

    LANGUAGE_MAP = {

        # Python
        ".py": "python",

        # JavaScript
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",

        # TypeScript
        ".ts": "typescript",
        ".tsx": "tsx",

        # Java
        ".java": "java",

        # C / C++
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",

        # Other languages (future expansion)
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "c_sharp"
    }

    @classmethod
    def detect_language(cls, file_path: str):

        extension = Path(file_path).suffix.lower()

        return cls.LANGUAGE_MAP.get(extension)

    @classmethod
    def is_supported(cls, file_path: str):

        return cls.detect_language(file_path) is not None
