"""Base Writer to write document results as HTML"""

import html
from io import IOBase, StringIO
from pathlib import Path
from typing import Optional, Union

from . import BaseWriter, SpanScheme
from ..result import DocResult, DocSectResult, MatchResult
from ..display import HTMLInlineSpanDelegate

DEFAULT_SPAN_COLOR = "#F1E740"  # dark yellow
"""Default color for span if scheme is missing a concept"""

DEFAULT_WRITER_OPTIONS = {
    # should have values for all possible keys, even if None, to simplify access
    "pretty_html": True,  # True for debugging
    "include_doc_name": True,  # Include doc name in output
}
"""Default document options for writer"""


class HTMLWriter(BaseWriter):
    """Writer to write document results as html

    Attributes:
      stream: Optional[IOBase]: Stream to write html, write string if None (Default value = None)
      scheme: SpanScheme: Scheme to use in generating spans (Default value = None)
      start_pad: int | None: Number of characters to include before a match (Default value = None)
      end_pad: int | None: Number of characters to include after a match (Default value = None)
      concept_colors: dict: Mapping from concept to it span color
      default_span_color: str: Default color for a span if scheme is missing a concept
      writer_options: dict: Dictionary of options for writer
      include_doc_name: bool: Whether to include the name of the document in the output
      delegate: HTMLWriterDelegate: Delegate to structure the document output

    Note: Delegate organizes the output by section, span, etc., and the Writer handles
          initiating the writing of a document and its sections and also the actual writing of
          tags and text to a stream
    """

    def __init__(
        self,
        stream: Optional[IOBase] = None,
        scheme: Union[SpanScheme, dict] = None,
        start_pad: Optional[int] = None,
        end_pad: Optional[int] = None,
    ):
        """
        Create a writer to write html to a stream

        Args:
          stream: Optional[IOBase]: Stream to write html, write string if None (Default value = None)
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
            print("WARN:", "Ignoring unknown scheme type for HTMLWriter: ", scheme)
            self.scheme = SpanScheme(start_pad=start_pad, end_pad=end_pad)
        self.start_pad = start_pad if start_pad is not None else self.scheme.start_pad
        self.end_pad = end_pad if start_pad is not None else self.scheme.end_pad
        self.concept_colors: dict = self.scheme.get("concept_colors", {})
        self.default_span_color: str = DEFAULT_SPAN_COLOR
        self.writer_options = {
            **DEFAULT_WRITER_OPTIONS,
            **self.scheme.get("writer_options", {}),
        }
        self.include_doc_name = self.scheme.get("include_doc_name", True)
        self.delegate = HTMLInlineSpanDelegate(self)

    def write_doc_result(self, item: DocResult):
        """
        Write document result

        Args:
          item: DocResult: Document result to write (via delegate)
        """
        self.delegate.start_doc(str(item.doc.name), item.all_results())
        for sect_result in item.sect_results:
            self.write_doc_section_result(sect_result)
        self.delegate.end_doc()

    def write_doc_section_result(self, item: DocSectResult):
        """
        Write document section result

        Args:
          item: DocSectResult: Document section result to write (via delegate)
        """
        start = item.start(pad=self.start_pad)
        end = item.end(pad=self.end_pad)
        # Sweep spans
        sweepd = DocResult.line_sweep_spans(item.results)
        self.delegate.start_section(item.results)
        current_index = start
        # span_stack = []
        for indx, d in sweepd.items():
            self.write_clean_text(item.doc.text[current_index:indx])
            self.delegate.write_span_end()
            if "e" in d:
                self.delegate.end_doc_span(d["e"])
            self.delegate.init_span()
            if "c" in d:
                self.delegate.continue_doc_span(d["c"])
            if "s" in d:
                self.delegate.start_doc_span(d["s"])
            self.delegate.write_span_start()
            current_index = indx
        self.write_clean_text(item.doc.text[current_index:end])
        self.delegate.end_section()

    def get_match_result_color(self, match_result: MatchResult) -> str:
        """
        Return the color for a match result concept

        Args:
          match_result: MatchResult: Match result with the concept to identify the color of

        Returns:
          str: Color to use for writing the concept result
        """
        return self.concept_colors.get(
            match_result.pattern.concept, self.default_span_color
        )

    def write_span_label(self, text: str):
        """
        Write span label

        Args:
          text: str: Span label
        """
        self.write(f"<sup>[{html.escape(text)}]</sup>")

    def write_clean_text(self, text: str):
        """
        Clean and write text (as escaped html)

        Args:
          text: str: Text to write
        """
        if self.writer_options["pretty_html"]:
            text = (
                text.replace("\n", " ")
                .replace("\r", " ")
                .replace("\f", " ")
                .replace("\t", " ")
            )
        self.write(html.escape(text))

    def write_tag(
        self,
        name: str,
        tag_args: dict = {},
        close: bool = False,
        singleton: bool = False,
        newline: bool = False,
    ):
        """
        Write an html tag to the instance's stream

        Args:
          name: str: Name of tag
          tag_args: dict:  Args of tag (Default value = {})
          close: bool: Whether this is closing the tag (Default value = False)
          singleton: bool: Whether the tag is only a singleton (so open and close) (Default value = False)
          newline: bool: Whether to add a newline at the end (Default value = False)
        """
        "Write html tag"
        arg_string = (
            " " + " ".join(k + "=" + f'"{v}"' for k, v in tag_args.items())
            if tag_args
            else ""
        )
        self.stream.write(
            "<"
            + ("/" if close else "")
            + name
            + arg_string
            + ("/" if singleton else "")
            + ">"
            + ("\n" if newline else "")
        )

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

    def get_doc_result_html(self, doc_result: DocResult) -> str:
        """
        Returns the html string for a single doc result at a time.
        This reuses a StringIO stream, but resets it before each use, and returns its str value

        Args:
          doc_result: DocResult: Document result to write as html

        Returns:
          str: HTML string of the formatted document result
        """
        assert isinstance(self.stream, StringIO)
        self.stream.seek(0)
        self.stream.truncate(0)
        self.write_doc_result(doc_result)
        return self.stream.getvalue()
