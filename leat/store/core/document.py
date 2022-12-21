"""Classes for Documents."""

from typing import Optional


class Document:
    "Basic document"

    def __init__(self, name: str, text: Optional[str] = ""):
        self.name = name
        self.text = text
