"""Basic regex pattern"""

import re
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

    def to_dict(self):
        d = {}
        d["concept"] = self.concept
        if self.pattern:
            d["pattern"] = self.pattern
        if self.regex is not None:
            d["regex"] = True
        d["flags"] = self.flags
        if self.source:
            d["source"] = self.source
        if self.metadata:
            d["metadata"] = self.metadata
        return d

    @classmethod
    def from_dict(cls, d):
        """Create a MatchPattern from a dict"""
        concept = d["concept"]
        pattern = d.get("pattern", "")
        flags = d.get("flags", 0)
        if d.get("regex", False):
            regex = re.compile(pattern, flags)
        else:
            regex = None
        source = d.get("source", "")
        metadata = d.get("metadata", {})
        return cls(concept, pattern, regex, flags, source, metadata)
