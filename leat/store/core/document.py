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
        if hasattr(self, "text_length") and not self.text:
            d["text_length"] = self.text_length
        else:
            d["text_length"] = len(self.text)
        if use_hash:
            if self.sha256 is None:
                if self.text:
                    self.sha256 = hashlib.sha256(self.text.encode())
                    d["sha256"] = self.sha256.hexdigest()
            else:
                if isinstance(self.sha256, str):
                    d["sha256"] = self.sha256
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
        text_length = d.get("text_length")
        if text_length is not None:
            if text and text_length != len(text):
                print(
                    "WARNING:",
                    f"Inconsistent text length {text_length} != {len(text)} for",
                    name,
                )
            else:
                doc.text_length = text_length
        return doc
