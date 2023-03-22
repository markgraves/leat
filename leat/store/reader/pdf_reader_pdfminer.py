"""Reader for pdf files."""

from pathlib import Path
from typing import Union

from pdfminer.high_level import extract_text

from . import BaseReader


class PDFReader(BaseReader):
    """Reader for pdf file"""

    def __init__(self, codec=None):
        """
        Create a reader for PDF files

        Args:
          codec: codec to use (Default value = None)

        Returns:

        """
        self.codec = codec

    def read(self, stream):
        """
        Extract pdf text from stream

        Args:
          stream: Stream to read from

        Returns:
          Text read from the stream
        """
        return extract_text(stream, codec=self.codec)

    def read_file(self, filename: Union[str, Path]):
        """
        Read text from pdf file

        Args:
          filename: Path | str: Filename to read from

        Returns:
          Text read from the file
        """
        return extract_text(filename, codec=self.codec)
