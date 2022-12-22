"""Base Writer to write document results"""

from abc import ABC
from io import IOBase
from pathlib import Path
from typing import Union


class BaseWriter(ABC):
    "Base Reader to write document results"

    def __init__(self, stream: IOBase):
        raise NotImplementedError()

    def write(self, text: str):
        "Write document result"
        raise NotImplementedError()

class SpanScheme():

    def __init__(self, start_pad=None, end_pad=None, **kwargs):
        self.start_pad = start_pad
        self.end_pad = end_pad
        self.data = kwargs

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __getitem__(self, key):
        return self.data[key]
