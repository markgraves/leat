"""Document Store. Isolates some file operations from the filesystem in which the files exist and from the readers that import the text from them."""

from pathlib import Path
from typing import Collection, Optional, Union

from . import Document, DocFile
from ..reader import TextReader, PDFReader, DocxReader


class DocStore:
    """Document Store that encapsulates file operations and the readers that import text from them.

    Attributes:
      filesys: "FileSys":  Filesystem from which document files are to be read
      filetypes: Collection[str] | None:  File types to be considered for reading

    Example:
      `ds = DocStore(LocalFileSys(filepath))`
    """

    supported_file_types = {"text", "pdf", "docx"}
    """File types supported by the document store"""

    def __init__(
        self, filesys: "FileSys" = None, filetypes: Optional[Collection[str]] = None
    ):
        """
        Creates a document store from a FileSys and optional collection of valid file types

        Args:
          filesys: FileSys: Filesystem from which document files are to be read (Default value = None)
          filetypes: Collection[str] | None: File types to be considered for reading (Default value = None)
        """
        self.filesys = filesys
        if filetypes is None:
            self.filetypes = self.__class__.supported_file_types.copy()
        else:
            self.filetypes = self.__class__.supported_file_types.intersection(filetypes)

    def read_documents(self):
        """Read and yield documents from the document store"""
        for file in self.filesys:
            yield self.read_document(file)

    def read_document(self, file: Union[Path, str]) -> Optional[Document]:
        """
        Read a document from the specified file

        Args:
          file: Path | str: File path to read document from

        Returns:
          Document with file and text, if file could be read, else None
        """
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
                elif filetype == "docx":
                    filepath = DocFile(file, filetype=filetype).get_file()
                    text = DocxReader().read_file(filepath)
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
        """Generator from read documents"""
        return self.read_documents()
