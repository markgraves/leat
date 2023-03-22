"""Reader for plain text file."""

from pathlib import Path
from typing import Union

from . import BaseReader


class TextReader(BaseReader):
    """Reader for plain text file"""

    def __init__(self, strip_whitespace: bool = False):
        """
        Create a reader for plain text

        Args:
          strip_whitespace: bool: Whether to strip whitespace (Default value = False)
        """
        self.strip_whitespace = strip_whitespace

    def read(self, stream):
        """
        Read plain text from a stream

        Args:
          stream: The stream

        Returns:
          Text read from the stream
        """
        return stream.read().strip() if self.strip_whitespace else stream.read()

    def read_file(self, filename: Union[str, Path], encoding: str = "utf-8"):
        """
        Read plain text from a file

        Args:
          filename: Path | str:  Filename to read from
          encoding: str: Encoding to use for reading (Default value = "utf-8")

        Returns:
          Text from the file
        """
        with open(filename, "r", encoding=encoding) as ifp:
            return self.read(ifp)
