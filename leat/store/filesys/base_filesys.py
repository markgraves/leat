"""Base FileSys to track files to be read."""

from abc import ABC
from pathlib import Path
from typing import Union


class BaseFileSys(ABC):
    "Base FileSys to track files to be read"

    def read_documents(self):
        "Read text from document files"
        raise NotImplementedError()
