
import json
import uuid

from pathlib import Path

from app.config import REPOSITORY_STORAGE_PATH
from app.parser.tree_sitter_parser import TreeSitterParser
from app.parser.symbol_extractor import SymbolExtractor


class RepositoryParser:

    def __init__(self):

        self.parser = TreeSitterParser()

    def get_syntax_errors(self, root_node):

        errors = []

        def traverse(node):

            if node.type == "ERROR" or node.is_missing:

                errors.append({
                    "node_type": node.type,
                    "start_line": node.start_point.row + 1,
                    "end_line": node.end_point.row + 1,
                    "is_missing": node.is_missing
                })

            for child in node.children:
                traverse(child)

        traverse(root_node)

        return errors

    def parse_repository(self, repository_id: str):

        # Validate repository ID
        try:
            repository_id = str(uuid.UUID(repository_id))
        except ValueError:
            raise ValueError("Invalid repository ID.")

        repository_path = (
            REPOSITORY_STORAGE_PATH / repository_id
        ).resolve()

        # Ensure path remains inside repository storage
        repository_path.relative_to(
            REPOSITORY_STORAGE_PATH.resolve()
        )

        if not repository_path.exists():
            raise FileNotFoundError(
                "Repository not found."
            )

        metadata_path = (
            repository_path / "repository_manifest.json"
        )

        if not metadata_path.exists():
            raise FileNotFoundError(
                "Repository manifest not found."
            )

        with open(
            metadata_path,
            "r",
            encoding="utf-8"
        ) as file:

            repository_metadata = json.load(file)

        parsed_files = []
        failed_files = []

        total_symbols = 0
        total_functions = 0
        total_classes = 0
        total_imports = 0
        total_calls = 0

        # Process every indexed source file
        for file_info in repository_metadata["files"]:

            relative_path = Path(
                file_info["file_path"]
            )

            # Prevent paths from escaping repository directory
            if relative_path.is_absolute() or ".." in relative_path.parts:
                failed_files.append({
                    "file_path": str(relative_path),
                    "error": "Unsafe file path"
                })
                continue

            source_path = (
                repository_path / relative_path
            ).resolve()

            try:
                source_path.relative_to(repository_path)
            except ValueError:
                failed_files.append({
                    "file_path": str(relative_path),
                    "error": "Path outside repository"
                })
                continue

            if not source_path.is_file():
                failed_files.append({
                    "file_path": str(relative_path),
                    "error": "Source file not found"
                })
                continue

            try:

                # Parse source file
                parse_result = self.parser.parse_file(
                    str(source_path)
                )

                # Extract symbols
                extractor = SymbolExtractor()

                extraction_result = extractor.extract(
                    root_node=parse_result["root_node"],
                    source_bytes=parse_result["source_bytes"],
                    file_path=relative_path.as_posix(),
                    language=parse_result["language"]
                )

                # Identify syntax errors
                syntax_errors = self.get_syntax_errors(
                    parse_result["root_node"]
                )

                file_result = {
                    **extraction_result,
                    "has_syntax_errors": parse_result["has_errors"],
                    "syntax_errors": syntax_errors
                }

                parsed_files.append(file_result)

                summary = extraction_result["summary"]

                total_symbols += summary["total_symbols"]
                total_functions += summary["total_functions"]
                total_classes += summary["total_classes"]
                total_imports += summary["total_imports"]
                total_calls += summary["total_calls"]

            except Exception as error:

                failed_files.append({
                    "file_path": relative_path.as_posix(),
                    "error": str(error)
                })

        # Generate repository-level AST metadata
        ast_manifest = {

            "repository_id": repository_id,

            "repository_name": repository_metadata[
                "repository_name"
            ],

            "commit_hash": repository_metadata[
                "commit_hash"
            ],

            "parsed_file_count": len(parsed_files),

            "failed_file_count": len(failed_files),

            "summary": {
                "total_symbols": total_symbols,
                "total_functions": total_functions,
                "total_classes": total_classes,
                "total_imports": total_imports,
                "total_calls": total_calls
            },

            "files": parsed_files,

            "failed_files": failed_files
        }

        # Save AST manifest
        output_path = (
            repository_path / "ast_manifest.json"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                ast_manifest,
                file,
                indent=4,
                ensure_ascii=False
            )

        return {
            "repository_id": repository_id,
            "parsed_file_count": len(parsed_files),
            "failed_file_count": len(failed_files),
            "summary": ast_manifest["summary"],
            "output_path": str(output_path)
        }
