import hashlib
from typing import Any

from app.chunking.token_counter import TokenCounter


class CodeChunker:

    def __init__(
        self,
        max_tokens: int = 1200,
        overlap_tokens: int = 120
    ):
        if max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero.")

        if overlap_tokens < 0 or overlap_tokens >= max_tokens:
            raise ValueError(
                "overlap_tokens must be non-negative "
                "and smaller than max_tokens."
            )

        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.token_counter = TokenCounter()

    @staticmethod
    def generate_chunk_id(
        file_path: str,
        qualified_name: str,
        chunk_index: int,
        code: str
    ) -> str:

        raw = (
            f"{file_path}:"
            f"{qualified_name}:"
            f"{chunk_index}:"
            f"{code}"
        )

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    def split_code(
        self,
        code: str,
        max_tokens: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Splits code at line boundaries.

        Each returned part contains its code and relative
        start/end line numbers. Oversized individual lines
        are split as a last resort.
        """

        limit = max_tokens or self.max_tokens

        if self.token_counter.count(code) <= limit:
            return [{
                "code": code,
                "start_line": 1,
                "end_line": max(1, len(code.splitlines()))
            }]

        lines = code.splitlines()
        parts = []

        current_lines = []
        current_tokens = 0
        current_start = 1

        def save_current():
            nonlocal current_lines, current_tokens, current_start

            if not current_lines:
                return

            parts.append({
                "code": "\n".join(current_lines),
                "start_line": current_start,
                "end_line": current_start + len(current_lines) - 1
            })

        for line_number, line in enumerate(lines, start=1):
            line_tokens = self.token_counter.count(line)

            # Handle an individual line that exceeds the limit.
            if line_tokens > limit:
                save_current()
                current_lines = []
                current_tokens = 0

                fragments = self._split_long_line(line, limit)

                for fragment in fragments:
                    parts.append({
                        "code": fragment,
                        "start_line": line_number,
                        "end_line": line_number
                    })

                current_start = line_number + 1
                continue

            if (
                current_lines
                and current_tokens + line_tokens > limit
            ):
                save_current()

                # Keep a small overlap from the previous chunk.
                overlap_lines = []
                overlap_count = 0

                for previous_line in reversed(current_lines):
                    previous_tokens = self.token_counter.count(
                        previous_line
                    )

                    if (
                        overlap_count + previous_tokens
                        > self.overlap_tokens
                    ):
                        break

                    overlap_lines.insert(0, previous_line)
                    overlap_count += previous_tokens

                current_lines = overlap_lines
                current_start = (
                    line_number - len(overlap_lines)
                )
                current_tokens = overlap_count

            if not current_lines:
                current_start = line_number

            current_lines.append(line)
            current_tokens += line_tokens

        save_current()

        return parts

    def _split_long_line(
        self,
        line: str,
        max_tokens: int
    ) -> list[str]:
        """Last-resort split for an exceptionally long source line."""

        if self.token_counter.encoder:
            tokens = self.token_counter.encoder.encode(line)

            return [
                self.token_counter.encoder.decode(
                    tokens[i:i + max_tokens]
                )
                for i in range(0, len(tokens), max_tokens)
            ]

        width = max_tokens * 4

        return [
            line[i:i + width]
            for i in range(0, len(line), width)
        ]

    def create_symbol_chunks(
        self,
        symbol: dict[str, Any],
        class_context: str | None = None
    ) -> list[dict[str, Any]]:

        symbol_code = symbol.get("code", "").strip()

        if not symbol_code:
            return []

        symbol_type = symbol.get("symbol_type", "function")
        qualified_name = symbol.get("qualified_name") or symbol.get(
            "name", "anonymous"
        )

        file_path = symbol.get("file_path", "")
        language = symbol.get("language", "unknown")

        # Add useful context to method chunks.
        prefix = ""

        if class_context:
            prefix = (
                f"Parent class context:\n"
                f"{class_context}\n\n"
            )

        complete_code = prefix + symbol_code

        pieces = self.split_code(complete_code)

        chunks = []

        for index, piece in enumerate(pieces):

            chunk_id = self.generate_chunk_id(
                file_path=file_path,
                qualified_name=qualified_name,
                chunk_index=index,
                code=piece["code"]
            )

            # Relative lines are adjusted to the symbol's
            # starting line. Context lines are excluded.
            context_line_count = len(prefix.splitlines()) if prefix else 0

            start_line = symbol.get("start_line", 1)
            end_line = symbol.get("end_line", start_line)

            if len(pieces) == 1:
                chunk_start = start_line
                chunk_end = end_line
            else:
                chunk_start = (
                    start_line
                    + max(0, piece["start_line"] - context_line_count - 1)
                )

                chunk_end = min(
                    end_line,
                    start_line
                    + max(0, piece["end_line"] - context_line_count - 1)
                )

            chunks.append({
                "chunk_id": chunk_id,
                "chunk_index": index,
                "chunk_type": symbol_type,
                "name": symbol.get("name"),
                "qualified_name": qualified_name,
                "code": piece["code"],
                "file_path": file_path,
                "language": language,
                "start_line": chunk_start,
                "end_line": chunk_end,
                "symbol_id": symbol.get("symbol_id"),
                "parent_symbol": symbol.get("parent_symbol"),
                "base_classes": symbol.get("base_classes", []),
                "parameters": symbol.get("parameters", []),
                "total_parts": len(pieces)
            })

        return chunks