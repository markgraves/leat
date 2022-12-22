"""Reader for plain text file."""

from pathlib import Path
from typing import Union

from . import BaseReader


class TextReader(BaseReader):
    "Reader for plain text file"

    def __init__(self, strip_whitespace: bool = False):
        self.strip_whitespace = strip_whitespace

    def read(self, stream):
        "Read plain text from stream"
        return stream.read().strip() if self.strip_whitespace else stream.read()

    def read_file(self, filename: Union[str, Path], encoding: str = "utf-8"):
        "Read plain text from text file"
        with open(filename, "r", encoding=encoding) as ifp:
            return self.read()
