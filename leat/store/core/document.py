"""Classes for Documents."""

import hashlib
from typing import Optional


class Document:
    "Basic document"

    def __init__(self, name: str, text: Optional[str] = ""):
        self.name = name
        self.text = text
        self.sha256 = None

    def to_dict(self, include_text=False, use_hash=True):
        d = {}
        d["name"] = self.name
        if include_text:
            d["text"] = self.text
        if use_hash:
            if self.sha256 is None:
                if self.text:
                    self.sha256 = hashlib.sha256(self.text.encode())
                    d["sha256"] = self.sha256.hexdigest()
            else:
                d["sha256"] = self.sha256.hexdigest()
        return d

    @classmethod
    def from_dict(cls, d):
        """Create a Document from a dict"""
        name = d.get("name", "")
        text = d.get("text", "")
        sha256 = d.get("sha256")
        doc = cls(name, text)
        doc.sha256 = sha256
        return doc
