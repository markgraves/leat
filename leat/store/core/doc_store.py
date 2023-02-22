"""Document Store. Isolates some file operations from the filesystem in which the files exist and from the readers that import the text from them."""

from pathlib import Path
from typing import Collection, Optional

from . import Document, DocFile
from ..reader import TextReader, PDFReader


class DocStore:
    """Document Store"""

    supported_file_types = {"text", "pdf"}

    def __init__(
        self, filesys: "FileSys" = None, filetypes: Optional[Collection[str]] = None
    ):
        self.filesys = filesys
        if filetypes is None:
            self.filetypes = self.__class__.supported_file_types.copy()
        else:
            self.filetypes = self.__class__.supported_file_types.intersection(filetypes)

    def read_documents(self):
        for file in self.filesys:
            yield self.read_document(file)

    def read_document(self, file):
        text = None
        if isinstance(file, str):
            file = Path(file)
        filetype = DocFile.get_file_type(file)
        if filetype and filetype in self.filetypes:
            try:
                if filetype in ["text", "md"]:
                    with DocFile(file, filetype=filetype).open_file() as ifp:
                        text = TextReader().read(ifp)
                elif filetype == "pdf":
                    with DocFile(file, filetype=filetype).open_file(mode="rb") as ifp:
                        text = PDFReader().read(ifp)
                else:
                    print("DEBUG:", "Unknown filetype", filetype, "for", file)
            except OSError:
                print("WARN:", "File could not be opened:", file)
        if text is not None:
            if len(text) == 0:
                print("INFO:", "Ignoring empty file:", file)
            else:
                doc = Document(file, text)
                return doc

    def __iter__(self):
        return self.read_documents()
