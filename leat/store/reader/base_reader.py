"""Base Reader to read and extract text from files"""

from abc import ABC
from pathlib import Path
from typing import Union


class BaseReader(ABC):
    "Base Reader to read and extract text from files"

    def read(self, filename: Union[str, Path]):
        "Read text from document file"
        raise NotImplementedError()
