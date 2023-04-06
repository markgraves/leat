"""Base Writer to write document results"""

from abc import ABC
from io import IOBase
from pathlib import Path
from typing import Union, Optional


class BaseWriter(ABC):
    """Base Reader to write document results"""

    def __init__(self, stream: IOBase):
        raise NotImplementedError()

    def write(self, text: str):
        "Write document result"
        raise NotImplementedError()


class SpanScheme:
    """Scheme for spans"""

    def __init__(
        self, start_pad: Optional[int] = None, end_pad: Optional[int] = None, **kwargs
    ):
        """
        Create a span scheme.
        For example, padding before and after results and colors for concept spans

        Args:
          start_pad:Optional[int]: Characters to include before result (Default value = None)
          end_pad:Optional[int]: Characters to include after result (Default value = None)
          **kwargs: Use to initialize data dict
        """
        self.start_pad = start_pad
        self.end_pad = end_pad
        self.data = kwargs

    def get(self, key, default=None):
        """
        Get from scheme data dict

        Args:
          key: Key
          default: Default if key is missing (Default value = None)

        Returns:
          Value from dict
        """
        return self.data.get(key, default)

    def __getitem__(self, key):
        return self.data[key]
