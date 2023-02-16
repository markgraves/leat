from .base_reader import BaseReader
from .text_reader import TextReader

try:
    from .pdf_reader_pdfminer import PDFReader
except ModuleNotFoundError:
    print("WARNING:", "PDF reading not available. Need to: pip install pdfminer")

    class PDFReader(BaseReader):
        def __init__(self, *args):
            print(
                "WARNING:", "PDF reading not available. Need to: pip install pdfminer"
            )

        def read(self, filename, *args):
            print(
                "WARNING:",
                "Cannot read PDF without package pdfminer for file:",
                filename,
            )
            return ""