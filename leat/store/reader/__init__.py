"""Reads and extracts text from different kinds of files"""

from .base_reader import BaseReader
from .text_reader import TextReader

try:
    from .pdf_reader_pdfminer import PDFReader
except ModuleNotFoundError:
    print("WARNING:", "PDF reading not available. Need to: pip install pdfminer.six")

    class PDFReader(BaseReader):
        """Stub for PDF reader"""

        def __init__(self, *args):
            print(
                "WARNING:",
                "PDF reading not available. Need to: pip install pdfminer.six",
            )

        def read(self, filename, *args):
            print(
                "WARNING:",
                "Cannot read PDF without package pdfminer.six for file:",
                filename,
            )
            return ""

try:
    from .docx_reader_docx2python import DocxReader
except ModuleNotFoundError:
     print("WARNING:", "PDF reading not available. Need to: pip install pdfminer.six")

     class DocxReader(BaseReader):
        """Stub for DOCX reader"""

        def __init__(self, *args):
            print(
                "WARNING:",
                "DOCX reading not available. Need to: pip install docx2python",
            )

        def read_file(self, filename, *args):
            print(
                "WARNING:",
                "Cannot read DOCX without package docx2python for file:",
                filename,
            )
       
