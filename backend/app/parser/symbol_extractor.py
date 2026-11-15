
import hashlib


class SymbolExtractor:

    FUNCTION_TYPES = {
        "function_definition",
        "function_declaration",
        "method_definition"
    }

    CLASS_TYPES = {
        "class_definition",
        "class_declaration",
        "abstract_class_declaration"
    }

    CALL_TYPES = {
        "call",
        "call_expression"
    }

    IMPORT_TYPES = {
        "import_statement",
        "import_from_statement"
    }

    def __init__(self):
        self.symbols = []
        self.imports = []
        self.calls = []
        self.source_bytes = b""
        self.file_path = ""
        self.language = ""

    # ----------------------------------
    # Basic node utilities
    # ----------------------------------

    def get_text(self, node):

        if node is None:
            return ""

        return self.source_bytes[
            node.start_byte:node.end_byte
        ].decode("utf-8", errors="replace")

    def get_field(self, node, field_name):

        return node.child_by_field_name(field_name)

    def get_line_range(self, node):

        start_line = node.start_point.row + 1

        # end_point is exclusive
        end_line = (
            node.end_point.row
            + (1 if node.end_point.column > 0 else 0)
        )

        end_line = max(start_line, end_line)

        return {
            "start_line": start_line,
            "end_line": end_line
        }

    def create_symbol_id(self, qualified_name, start_line):

        raw = (
            f"{self.file_path}:"
            f"{qualified_name}:"
            f"{start_line}"
        )

        return hashlib.sha1(
            raw.encode("utf-8")
        ).hexdigest()[:16]

    # ----------------------------------
    # Function name extraction
    # ----------------------------------

    def get_function_name(self, node):

        name_node = self.get_field(node, "name")

        if name_node:
            return self.get_text(name_node)

        # Handle JavaScript arrow functions and
        # function expressions assigned to variables.
        current = node.parent

        while current is not None:

            if current.type == "variable_declarator":

                name_node = self.get_field(
                    current,
                    "name"
                )

                if name_node:
                    return self.get_text(name_node)

            if current.type == "assignment":

                left_node = self.get_field(
                    current,
                    "left"
                )

                if left_node:
                    return self.get_text(left_node)

            if current.type in {
                "expression_statement",
                "program",
                "module",
                "class_body"
            }:
                break

            current = current.parent

        return "<anonymous>"

    # ----------------------------------
    # Parameter extraction
    # ----------------------------------

    def get_parameters(self, node):

        parameters_node = self.get_field(
            node,
            "parameters"
        )

        if parameters_node is None:
            parameters_node = self.get_field(
                node,
                "parameter"
            )

        if parameters_node is None:
            return []

        parameters = []

        for child in parameters_node.named_children:

            if child.type in {
                "comment",
                "type_annotation"
            }:
                continue

            parameters.append(
                self.get_text(child).strip()
            )

        return parameters

    # ----------------------------------
    # Class inheritance
    # ----------------------------------

    def get_base_classes(self, node):

        if self.language == "python":

            base_node = self.get_field(
                node,
                "superclasses"
            )

            if base_node:
                return [
                    self.get_text(child).strip()
                    for child in base_node.named_children
                ]

        elif self.language in {
            "javascript",
            "typescript",
            "tsx"
        }:

            for child in node.named_children:

                if child.type in {
                    "class_heritage",
                    "extends_clause"
                }:

                    return [
                        self.get_text(child).strip()
                    ]

        return []

    # ----------------------------------
    # Import extraction
    # ----------------------------------

    def extract_import(self, node):

        import_text = self.get_text(node).strip()

        import_info = {
            "file_path": self.file_path,
            "language": self.language,
            "import_type": node.type,
            "statement": import_text,
            **self.get_line_range(node)
        }

        self.imports.append(import_info)

    # ----------------------------------
    # Function call extraction
    # ----------------------------------

    def extract_call(
        self,
        node,
        enclosing_symbol
    ):

        function_node = self.get_field(
            node,
            "function"
        )

        if function_node is None:
            return

        function_name = self.get_text(
            function_node
        ).strip()

        if not function_name:
            return

        call_info = {
            "caller": enclosing_symbol,
            "callee": function_name,
            "file_path": self.file_path,
            **self.get_line_range(node)
        }

        self.calls.append(call_info)

    # ----------------------------------
    # Symbol extraction
    # ----------------------------------

    def extract_symbol(
        self,
        node,
        parent_symbol=None
    ):

        symbol_type = None

        if node.type in self.CLASS_TYPES:

            symbol_type = "class"

        elif node.type in self.FUNCTION_TYPES:

            symbol_type = "function"

        elif (
            node.type == "arrow_function"
            or node.type == "function_expression"
        ):

            # Only extract arrow/function expressions
            # when they are assigned to a named variable
            name = self.get_function_name(node)

            if name != "<anonymous>":
                symbol_type = "function"

        if symbol_type is None:
            return None

        if symbol_type == "class":

            name_node = self.get_field(
                node,
                "name"
            )

            if name_node is None:
                return None

            name = self.get_text(name_node)

        else:

            name = self.get_function_name(node)

        if parent_symbol:

            qualified_name = (
                f"{parent_symbol}.{name}"
            )

        else:

            qualified_name = name

        lines = self.get_line_range(node)

        symbol_id = self.create_symbol_id(
            qualified_name,
            lines["start_line"]
        )

        symbol = {
            "symbol_id": symbol_id,
            "name": name,
            "qualified_name": qualified_name,
            "symbol_type": symbol_type,
            "file_path": self.file_path,
            "language": self.language,
            "parent_symbol": parent_symbol,
            "parameters": (
                self.get_parameters(node)
                if symbol_type == "function"
                else []
            ),
            "base_classes": (
                self.get_base_classes(node)
                if symbol_type == "class"
                else []
            ),
            "code": self.get_text(node),
            **lines
        }

        self.symbols.append(symbol)

        return qualified_name

    # ----------------------------------
    # Recursive tree traversal
    # ----------------------------------

    def walk(
        self,
        node,
        current_symbol=None
    ):

        # Extract import statements
        if node.type in self.IMPORT_TYPES:

            self.extract_import(node)

        # Extract function calls
        if node.type in self.CALL_TYPES:

            self.extract_call(
                node,
                current_symbol
            )

        # Extract functions and classes
        new_symbol = self.extract_symbol(
            node,
            current_symbol
        )

        if new_symbol:

            current_symbol = new_symbol

        # Traverse children
        for child in node.named_children:

            self.walk(
                child,
                current_symbol
            )

    # ----------------------------------
    # Main extraction function
    # ----------------------------------

    def extract(
        self,
        root_node,
        source_bytes,
        file_path,
        language
    ):

        self.symbols = []
        self.imports = []
        self.calls = []

        self.source_bytes = source_bytes
        self.file_path = file_path
        self.language = language

        self.walk(root_node)

        return {
            "file_path": file_path,
            "language": language,
            "symbols": self.symbols,
            "imports": self.imports,
            "calls": self.calls,
            "summary": {
                "total_symbols": len(self.symbols),
                "total_functions": sum(
                    s["symbol_type"] == "function"
                    for s in self.symbols
                ),
                "total_classes": sum(
                    s["symbol_type"] == "class"
                    for s in self.symbols
                ),
                "total_imports": len(self.imports),
                "total_calls": len(self.calls)
            }
        }
