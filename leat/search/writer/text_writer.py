"""Base Writer to write document results at Text"""

from io import IOBase, StringIO
from pathlib import Path
from typing import Optional, Union

from . import BaseWriter, SpanScheme
from ..result import DocResult, DocSectResult, MatchResult


class TextWriter(BaseWriter):
    """Base Reader to write document results as text

    Attributes:
      stream: Optional[IOBase]: Stream to write text, write string if None
      scheme: SpanScheme: Scheme to use in generating spans
      start_pad: int | None: Number of characters to include before a match
      end_pad: int | None: Number of characters to include after a match
      uppercase_match: bool: Whether to uppercase the matched text upon output

    Note: Delegate organizes the output by section, span, etc., and the Writer handles
          initiating the writing of a document and its sections and also the actual writing of
          text to a stream

    """

    def __init__(
        self,
        stream: Optional[IOBase] = None,
        scheme: Union[SpanScheme, dict] = None,
        start_pad: Optional[int] = None,
        end_pad: Optional[int] = None,
    ):
        """
        Create a text writer to write text to a stream

        Args:
          stream: Optional[IOBase]: Stream to write text, write string if None (Default value = None)
          scheme: SpanScheme | dict: Scheme to use in generating spans (Default value = None)
          start_pad: int | None: Number of characters to include before a match (Default value = None)
          end_pad: int | None: Number of characters to include after a match (Default value = None)
        """
        if stream is not None:
            self.stream = stream
        else:
            self.stream = StringIO()
        if scheme is None:
            self.scheme = SpanScheme(start_pad=start_pad, end_pad=end_pad)
        elif isinstance(scheme, dict):
            self.scheme = SpanScheme(**scheme)
        elif isinstance(scheme, SpanScheme):
            self.scheme = scheme
        else:
            print("WARN:", "Ignoring unknown scheme type for TextWriter: ", scheme)
            self.scheme = SpanScheme(start_pad=start_pad, end_pad=end_pad)
        self.start_pad = start_pad if start_pad is not None else self.scheme.start_pad
        self.end_pad = end_pad if start_pad is not None else self.scheme.end_pad
        self.uppercase_match = self.scheme.get("uppercase_match", True)

    def write_doc_result(self, item: DocResult):
        """
        Write document result

        Args:
          item: DocResult: Document result to write (via delegate)
        """
        self.write(str(item.doc.name))
        self.write_line()
        for sect_result in item.sect_results:
            self.write_doc_section_result(sect_result)

    def write_doc_section_result(self, item: DocSectResult):
        """
         Write document section result

        Args:
          item: DocSectResult: Document section result to write (via delegate)
        """
        start = item.start(pad=self.start_pad)
        end = item.end(pad=self.end_pad)
        self.write_clean_text(item.doc.text[start:end])
        self.write_line()
        for mr in item.results:
            mrtext = mr.astext(uppercase_match=self.uppercase_match)
            self.write_line(" " * (mr.start - start) + mrtext)

    def write_clean_text(self, text: str):
        """
        Clean and write text

        Args:
          text: str: Text to write
        """
        text = (
            text.replace("\n", " ")
            .replace("\r", " ")
            .replace("\f", " ")
            .replace("\t", " ")
        )
        self.write(text)

    def write_line(self, text: Optional[str] = None):
        """
        Write a line of text (with a newline at the end)

        Args:
          text: Optional[str]: Text to write (Default value = None)
        """
        if text is not None:
            self.stream.write(text)
        self.stream.write("\n")

    def write(self, text: str):
        """
        Write text to the instance's stream (and do nothing else)

        Args:
          text: str: Text to write
        """
        self.stream.write(text)
