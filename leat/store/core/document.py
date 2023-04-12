"""Classes for Documents."""

import hashlib
from typing import Optional


class Document:
    """
    Basic document with name and text

    Attributes:
      name: str: Name of the document
      text: Optional[str]: Text from the document
      sha256: sha256 hash of the text (created in :meth:`to_dict`)
    """

    def __init__(self, name: str, text: Optional[str] = ""):
        """
        Create a basic document with name and text

        Args:
          name: str: Name of the document
          text: str | None: Text from the document (Default value = "")
        """
        self.name = name
        self.text = text
        self.sha256 = None

    def to_dict(self, include_text: bool = False, use_hash: bool = True) -> dict:
        """
        Create dict from Document

        Args:
          include_text: bool: Include text in dictionary (Default value = False)
          use_hash: bool: Use hash for text (generate sha256 hash as needed) (Default value = True)

        Returns:
          dict: The created dictionary
        """
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
    def from_dict(cls, dictionary: dict) -> "Document":
        """
        Create a Document from a dict

        Args:
          dictionary: dict: Dictionary created by :meth:`~to_dict`

        Returns:
          Document: Document created from the dict
        """
        name = dictionary.get("name", "")
        text = dictionary.get("text", "")
        sha256 = dictionary.get("sha256")
        doc = cls(name, text)
        doc.sha256 = sha256
        text_length = dictionary.get("text_length")
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
