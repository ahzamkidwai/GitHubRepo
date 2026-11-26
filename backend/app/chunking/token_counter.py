class TokenCounter:
    """
    Counts tokens using tiktoken when installed.
    Falls back to a character-based estimate otherwise.

    Note: cl100k_base is an approximation for code and is
    not guaranteed to match your eventual embedding model.
    """

    def __init__(self):
        self.encoder = None

        try:
            import tiktoken
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            pass

    def count(self, text: str) -> int:
        if not text:
            return 0

        if self.encoder:
            return len(self.encoder.encode(text))

        # Rough fallback: approximately 1 token per 4 characters.
        return max(1, len(text) // 4)

    def truncate(self, text: str, max_tokens: int) -> str:
        if self.count(text) <= max_tokens:
            return text

        if self.encoder:
            tokens = self.encoder.encode(text)
            return self.encoder.decode(tokens[:max_tokens])

        # Character-based fallback.
        return text[:max_tokens * 4]