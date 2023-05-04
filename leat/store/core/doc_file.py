"""Document File. Isolates some file operations from the filesystem in which the files exist."""

from pathlib import Path
from typing import Optional, Union

FILE_EXTENSION_TYPES = {
    "md": "md",
    "pdf": "pdf",
    "text": "text",
    "txt": "text",
    "docx": "docx",
}
"""dict: Mapping from file extensions to file type"""


class DocFile:
    """
    Document File wrapper to a file path that includes file type and encapsulates file system dependencies

    Attributes:
      filepath: Path: Path to the file
      filetype: str: Type of the file (e.g., pdf, text), either specified or derived from file extension
    """

    def __init__(self, filepath: Path, filetype: Optional[str] = None):
        """
        Create a DocFile from a file path

        Args:
          filepath: Path: Path to the file
          filetype: str | None: Type of the file (e.g., pdf, text) (Default value = None)
        """
        self.filepath = filepath
        if filetype is None:
            self.filetype = self.get_file_type(filepath)
        else:
            self.filetype = filetype

    @classmethod
    def get_file_type(cls, filename: Union[Path, str]) -> Optional[str]:
        """
        Get the type of a file from its extention

        Args:
          filename: Path | str: name or path of a file

        Returns:
          str | None: file type
        """
        fileext = cls.get_file_extension(filename)
        if not fileext:
            return None
        return FILE_EXTENSION_TYPES.get(fileext)

    @classmethod
    def get_file_extension(cls, filename: Union[Path, str]) -> str:
        """
        Get the extension of a file (without the ".")

        Args:
          filename: Path | str: name or path of a file

        Returns:
          str: The file extension, if it exists, else ''
        """
        "Get type of file from its extension"
        return Path(filename).suffix.strip(".")

    def valid_file(self) -> bool:
        """Returns True iff file is a file and has a file type"""
        return self.filepath.is_file() and self.filetype

    def open_file(self, mode: str = "r", *args):
        """
        Wrapper for open, checking if file is valid first

        Args:
          mode: str: Passed to open (Default value = "r")
          *args: Passed to open

        Returns:
          File pointer (like open) if valid, else None
        """
        if self.valid_file():
            return open(self.filepath, mode=mode, *args)
        return None

    def get_file(self):
        """
        Wrapper for getting filepath, checking if file is valid first

        Returns:
          File path if valid, else None
        """
        if self.valid_file():
            return self.filepath
        return None
    
