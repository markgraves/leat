"""Reader for docx files using docx2python."""

from pathlib import Path
from typing import Union

from docx2python import docx2python

from . import BaseReader


class DocxReader(BaseReader):
    """Reader for pdf file"""

    def __init__(self, html: bool = False):
        """
        Create a reader for DOCX files

        Args:
          html: bool: return text as html (Default value = False)

        Returns:

        """
        self.return_html = html

    def read(self, stream):
        """
        Extract docx text from stream

        Args:
          stream: Stream to read from

        Returns:
          Text read from the stream
        """
        raise NotImplementedError

    def read_file(self, filename: Union[str, Path]):
        """
        Read text from docx file

        Args:
          filename: Path | str: Filename to read from

        Returns:
          Text read from the file
        """
        with docx2python(filename, html=self.return_html) as docx_content:
            return docx_content.text
