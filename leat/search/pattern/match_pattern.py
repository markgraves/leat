"""Basic regex pattern"""

import re
from typing import Optional


class MatchPattern:
    """Basic regex pattern

    Attributes:
      concept: str: Concept which uses the pattern
      pattern: str: String version of the pattern
      regex: Compiled regex (regular expression object) for the pattern
      flags: int: Flags to use in compiling the match pattern
      source: str: Source configuration file for the match pattern
      metadata: dict: Dictionary of auxillary information

    """

    def __init__(
        self,
        concept: str,
        pattern: Optional[str] = "",
        regex=None,
        flags: int = 0,
        source: str = "",
        metadata: dict = {},
    ):
        """
        Create a regular expression pattern for a concept

        Args:
          concept: str: Concept which uses the pattern
          pattern: Optional[str]: String version of the pattern (Default value = "")
          regex: Compiled regex for the pattern. If None, will compile from pattern and flags (Default value = None)
          flags: int: Flags to use when compiling the match pattern (Default value = 0)
          source: str: Source configuration file for the match pattern (Default value = "")
          metadata: dict: Dictionary of auxillary information (Default value = {})
        """
        self.concept = concept
        self.pattern = pattern
        if regex is not None:
            self.regex = regex
        else:
            self.regex = re.compile(pattern, flags)
        self.flags = flags
        self.source = source
        self.metadata = metadata

    def __str__(self):
        """ """
        return f'<{__class__.__name__} {self.concept} "{self.pattern[:20]}">'

    def finditer(self, text: str, *args, **kwargs):
        """
        Create an iterator of matches in the text

        Args:
          text: str: Text in which to search for the pattern
          *args:  Passed to re.finditer
          **kwargs:  Passed to re.finditer

        Returns:
          An interator that yields matches found in the text
        """
        return self.regex.finditer(text, *args, **kwargs)

    def to_dict(self):
        """Convert the MatchPattern object instance to a dict"""
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
    def from_dict(cls, d: dict):
        """
        Create a MatchPattern from a dict

        Args:
          d: dict: Dict form of the MatchPattern

        Returns:
          Instance of MatchPattern
        """
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
