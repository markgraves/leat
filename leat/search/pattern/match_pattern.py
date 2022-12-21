"""Basic regex pattern"""

from typing import Optional


class MatchPattern:
    "Basic regex pattern"

    def __init__(
        self,
        concept: str,
        pattern: Optional[str] = "",
        regex=None,
        flags: int = 0,
        source: str = "",
        metadata: dict = {},
    ):
        self.concept = concept
        self.pattern = pattern
        self.regex = regex
        self.flags = flags
        self.source = source
        self.metadata = metadata

    def __str__(self):
        return f'<{__class__.__name__} {self.concept} "{self.pattern[:20]}">'

    def finditer(self, text, *args, **kwargs):
        return self.regex.finditer(text, *args, **kwargs)
