"""Document File. Isolates some file operations from the filesystem in which the files exist."""

from pathlib import Path
from typing import Optional

FILE_EXTENSION_TYPES = {
    "md": "md",
    "pdf": "pdf",
    "text": "text",
    "txt": "text",
}


class DocFile:
    """Document File"""

    def __init__(self, filepath: Path, filetype: Optional[str] = None):
        self.filepath = filepath
        if filetype is None:
            self.filetype = self.get_file_type(filepath)
        else:
            self.filetype = filetype

    @classmethod
    def get_file_type(cls, filename):
        "Get type of file"
        filetype = cls.get_extension_type(filename)
        return filetype

    @classmethod
    def get_extension_type(cls, filename):
        "Get type of file from its extension"
        fileext = Path(filename).suffix.strip(".")
        if not fileext:
            return None
        return FILE_EXTENSION_TYPES.get(fileext)

    def valid_file(self):
        return self.filepath.is_file() and self.filetype

    def open_file(self, mode="r", *args):
        if self.valid_file():
            return open(self.filepath, mode=mode, *args)
        return None
