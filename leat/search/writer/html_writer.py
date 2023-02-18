"""Base Writer to write document results as HTML"""

import html
from io import IOBase, StringIO
from pathlib import Path
from typing import Optional, Union

from . import BaseWriter, SpanScheme
from ..result import DocResult, DocSectResult, MatchResult
from ..display import HTMLInlineSpanDelegate

DEFAULT_SPAN_COLOR = "#F1E740"  # dark yellow

DEFAULT_WRITER_OPTIONS = {
    # should have values for all possible keys, even if None, to simplify access
    "pretty_html": True,  # True for debugging
    "include_doc_name": True,  # Include doc name in output
}


class HTMLWriter(BaseWriter):
    "Base Reader to write document results as html"

    def __init__(
        self, stream: Optional[IOBase] = None, scheme=None, start_pad=None, end_pad=None
    ):
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
        self.concept_colors = self.scheme.get("concept_colors", {})
        self.default_span_color = DEFAULT_SPAN_COLOR
        self.writer_options = {
            **DEFAULT_WRITER_OPTIONS,
            **self.scheme.get("writer_options", {}),
        }
        self.include_doc_name = self.scheme.get("include_doc_name", True)
        self.delegate = HTMLInlineSpanDelegate(self)

    def write_doc_result(self, item: DocResult):
        "Write document result"
        self.delegate.start_doc(str(item.doc.name), item.all_results())
        for sect_result in item.sect_results:
            self.write_doc_section_result(sect_result)
        self.delegate.end_doc()

    def write_doc_section_result(self, item: DocSectResult):
        "Write document section result"
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

    def get_match_result_color(self, match_result):
        "Return the color for a match result concept"
        return self.concept_colors.get(
            match_result.pattern.concept, self.default_span_color
        )

    def write_span_label(self, text: str):
        "Write span label"
        self.write(f"<sup>[{html.escape(text)}]</sup>")

    def write_clean_text(self, text: str):
        "Clean and write text"
        if self.writer_options["pretty_html"]:
            text = (
                text.replace("\n", " ")
                .replace("\r", " ")
                .replace("\f", " ")
                .replace("\t", " ")
            )
        self.write(html.escape(text))

    def write_tag(
        self, name: str, tag_args={}, close=False, singleton=False, newline=False
    ):
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
        "Write line"
        if text is not None:
            self.stream.write(text)
        self.stream.write("\n")

    def write(self, text: str):
        "Write text"
        self.stream.write(text)

    def get_doc_result_html(self, doc_result: DocResult):
        "Returns the html string for a single doc result at a time"
        assert isinstance(self.stream, StringIO)
        self.stream.seek(0)
        self.stream.truncate(0)
        self.write_doc_result(doc_result)
        return self.stream.getvalue()
