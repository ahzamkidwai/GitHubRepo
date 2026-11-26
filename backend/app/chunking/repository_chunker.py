import json
import uuid

from pathlib import Path
from typing import Any

from app.config import REPOSITORY_STORAGE_PATH
from app.chunking.code_chunker import CodeChunker


class RepositoryChunker:

    def __init__(self):
        self.chunker = CodeChunker(
            max_tokens=1200,
            overlap_tokens=120
        )

    def validate_repository_id(self, repository_id: str):
        try:
            uuid.UUID(repository_id)
        except ValueError as error:
            raise ValueError("Invalid repository ID.") from error

    def get_repository_path(self, repository_id: str) -> Path:

        self.validate_repository_id(repository_id)

        storage_root = Path(
            REPOSITORY_STORAGE_PATH
        ).resolve()

        repository_path = (
            storage_root / repository_id
        ).resolve()

        try:
            repository_path.relative_to(storage_root)
        except ValueError as error:
            raise ValueError(
                "Invalid repository storage path."
            ) from error

        if not repository_path.is_dir():
            raise FileNotFoundError(
                f"Repository not found: {repository_id}"
            )

        return repository_path

    def load_ast_manifest(
        self,
        repository_path: Path
    ) -> dict[str, Any]:

        manifest_path = repository_path / "ast_manifest.json"

        if not manifest_path.exists():
            raise FileNotFoundError(
                "AST manifest not found. "
                "Run Module 2 parsing before chunking."
            )

        with manifest_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def build_class_context(symbol: dict) -> str:
        """Create a concise context header for a class."""

        class_name = symbol.get("qualified_name") or symbol.get(
            "name", "UnknownClass"
        )

        base_classes = symbol.get("base_classes", [])

        context = f"class {class_name}"

        if base_classes:
            context += (
                "(" + ", ".join(base_classes) + ")"
            )

        return context

    def process_file(
        self,
        file_data: dict[str, Any]
    ) -> list[dict[str, Any]]:

        symbols = file_data.get("symbols", [])

        class_contexts = {}
        chunks = []

        # First pass: collect class context.
        for symbol in symbols:

            if symbol.get("symbol_type") == "class":
                class_contexts[
                    symbol.get("qualified_name")
                    or symbol.get("name")
                ] = self.build_class_context(symbol)

        # Second pass: create chunks.
        for symbol in symbols:

            # symbol_type = symbol.get("symbol_type")

            # parent_symbol = symbol.get("parent_symbol")

            # class_context = None

            # if symbol_type == "method" or parent_symbol:
            #     class_context = class_contexts.get(parent_symbol)

            symbol_type = symbol.get("symbol_type")

            parent_symbol = symbol.get("parent_symbol")
            
            class_context = None
            
            # A function with a parent symbol is a class method.
            if parent_symbol:
                class_context = class_contexts.get(parent_symbol)
            
                # Normalize the type for downstream retrieval.
                if symbol_type == "function":
                    symbol["symbol_type"] = "method"

            symbol_chunks = self.chunker.create_symbol_chunks(
                symbol=symbol,
                class_context=class_context
            )

            chunks.extend(symbol_chunks)

        return chunks

    def chunk_repository(
        self,
        repository_id: str
    ) -> dict[str, Any]:

        repository_path = self.get_repository_path(
            repository_id
        )

        ast_manifest = self.load_ast_manifest(
            repository_path
        )

        all_chunks = []

        files = ast_manifest.get("files", [])

        for file_data in files:

            try:
                file_chunks = self.process_file(file_data)
                all_chunks.extend(file_chunks)

            except Exception as error:
                print(
                    f"Could not chunk "
                    f"{file_data.get('file_path')}: {error}"
                )

        # Create chunk statistics.
        chunk_types = {}

        for chunk in all_chunks:
            chunk_type = chunk["chunk_type"]

            chunk_types[chunk_type] = (
                chunk_types.get(chunk_type, 0) + 1
            )

        output = {
            "repository_id": repository_id,
            "repository_name": ast_manifest.get(
                "repository_name"
            ),
            "commit_hash": ast_manifest.get("commit_hash"),
            "total_chunks": len(all_chunks),
            "chunk_types": chunk_types,
            "chunks": all_chunks
        }

        output_path = repository_path / "chunks_manifest.json"

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(
                output,
                file,
                indent=2,
                ensure_ascii=False
            )

        return {
            "repository_id": repository_id,
            "repository_name": output["repository_name"],
            "total_chunks": len(all_chunks),
            "chunk_types": chunk_types,
            "output_path": str(output_path)
        }