
from tree_sitter import Parser
from tree_sitter_language_pack import get_language

from app.parser.language_detector import LanguageDetector


class TreeSitterParser:

    def __init__(self):

        self.parser_cache = {}

    def get_parser(self, language_name: str):

        """
        Create and cache a parser for a language.
        """

        if language_name not in self.parser_cache:

            language = get_language(language_name)

            self.parser_cache[language_name] = Parser(language)

        return self.parser_cache[language_name]

    def parse_source(
        self,
        source_code: str,
        language_name: str
    ):

        """
        Parse source code and return the syntax tree.
        """

        parser = self.get_parser(language_name)

        source_bytes = source_code.encode("utf-8")

        tree = parser.parse(source_bytes)

        if tree is None:
            raise RuntimeError(
                f"Tree-sitter failed to parse {language_name} source."
            )

        root_node = tree.root_node

        return {
            "tree": tree,
            "root_node": root_node,
            "has_errors": root_node.has_error,
            "source_bytes": source_bytes
        }

    def parse_file(self, file_path: str):

        """
        Read a source file, detect its language,
        and generate its syntax tree.
        """

        language_name = LanguageDetector.detect_language(
            file_path
        )

        if not language_name:

            raise ValueError(
                f"Unsupported programming language: {file_path}"
            )

        with open(file_path, "rb") as file:
            source_bytes = file.read()

        # Preserve source bytes for accurate AST offsets
        source_code = source_bytes.decode(
            "utf-8",
            errors="replace"
        )

        result = self.parse_source(
            source_code,
            language_name
        )

        return {
            **result,
            "language": language_name,
            "source_code": source_code,
            "file_path": file_path
        }
