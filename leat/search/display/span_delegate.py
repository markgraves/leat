"""Delegate writer code for match result"""

from abc import ABC
from collections import Counter
import html
from typing import Sequence

from ..result import MatchResult  # for typing only
from .colors import mix_hex_color_strings


class BaseWriterDelegate(ABC):
    """Base Writer Delegate"""

    def start_section(self):
        pass

    def end_section(self):
        pass

    def init_span(self):
        pass

    def start_doc_span(self, match_results: Sequence["MatchResult"]):
        pass

    def end_doc_span(self, match_results: Sequence["MatchResult"]):
        pass

    def continue_doc_span(self, match_results: Sequence["MatchResult"]):
        pass

    def write_span_start(self):
        pass

    def write_span_end(self):
        pass


class HTMLInlineSpanDelegate(BaseWriterDelegate):
    """Delegates writing inline html spans for match result

    Attributes:
      writer: HTMLWriter: Writer to use for generating html
      details_summary: bool: Whether to create details/summary section
      collapse_section: bool: If details_summary, collapse section
      collapse_section_default_open: bool
      tag_args_document_details: dict: Args for detail tag
      tag_args_document_summary: dict: Args for summary tag
    """

    def __init__(self, writer: "HTMLWriter"):
        """
        Create an object that writes inline html spans using the writer

        Args:
          writer: "HTMLWriter": Writer to use for generating html

        """
        self.writer = writer
        wopts = self.writer.writer_options
        self.details_summary: bool = wopts.get("details_summary", True)
        if self.details_summary:
            self.collapse_section: bool = wopts.get("collapse_section", True)
            self.collapse_section_default_open: bool = wopts.get(
                "collapse_section_default_open", True
            )
            self.collapse_document: bool = wopts.get("collapse_document", True)
            self.tag_args_document_details: dict = {
                "style": "margin-left: 2em;",
                **wopts.get("tag_args_document_details", {}),
            }
            self.tag_args_document_summary: dict = {
                "style": "margin-left: -2em;",
                **wopts.get("tag_args_document_summary", {}),
            }
        else:
            self.collapse_section = False
            self.collapse_document = False

    def start_doc(
        self,
        name: str,
        match_results: Sequence["MatchResult"] = None,
        html_output: bool = True,
    ):
        """
        Write tags to start the document output, which will dispay the match results

        Args:
          name: str: Name of the document
          match_results: Sequence["MatchResult"]: Match results for the document (Default value = None)
          html_output: bool: Whether to generate as html (or plain text)  (Default value = True)
        """
        self.writer.write_tag("div", newline=True)
        if self.writer.writer_options["include_doc_name"]:
            self.writer.write(name)
            self.writer.write_line()
        if self.collapse_document:
            self.writer.write_tag("details", tag_args=self.tag_args_document_details)
            if match_results is not None:
                self.writer.write_tag(
                    "summary", tag_args=self.tag_args_document_summary
                )
                self.writer.write(
                    self.summarize_results(
                        match_results, html_output=True, max_num_concepts=9
                    )
                )
                self.writer.write_tag("summary", close=True)

    def end_doc(self):
        """Write tags to end the document output"""
        if self.collapse_document:
            self.writer.write_tag("details", close=True)
        self.writer.write_tag("div", close=True, newline=True)

    def start_section(self, match_results: Sequence["MatchResult"] = None):
        """
        Write tags to start section, and maybe summarize match_results

        Args:
          match_results: Sequence[MatchResult]: Match results for the section (Default value = None)
        """
        self.writer.write_tag("div", newline=True)
        if self.collapse_section and match_results is not None:
            if self.collapse_section_default_open:
                self.writer.write("<details open>")
            else:
                self.writer.write_tag("details")
            self.writer.write_tag("summary")
            self.writer.write(self.summarize_results(match_results, html_output=True))
            self.writer.write_tag("summary", close=True)
        self.writer.write_tag("span")

    def end_section(self):
        """Write tags to end section"""
        self.writer.write_tag("span", close=True)
        if self.collapse_section:
            self.writer.write_tag("details", close=True)
        self.writer.write_tag("div", close=True, newline=True)

    def init_span(self):
        """Initialize a span"""
        self.tooltip = []
        self.base_color = None
        self.span_color = None

    def start_doc_span(self, match_results: Sequence["MatchResult"]):
        """
        Start a doc span

        Args:
          match_results: Sequence[MatchResult]: Match results for the doc span
        """
        if not match_results:
            return
        self.span_color = mix_hex_color_strings(
            list(self.writer.get_match_result_color(mr) for mr in match_results)
        )
        self.tooltip.extend(mr.pattern.concept for mr in match_results)

    def end_doc_span(self, match_results: Sequence["MatchResult"]):
        """
        End a doc span

        Args:
          match_results: Sequence[MatchResult]: Match results for the doc span
        """
        for mr in match_results:
            self.writer.write_tag(
                "span",
                tag_args={
                    "style": "color:" + self.writer.get_match_result_color(mr),
                    "title": mr.astext(),
                },
            )
            self.writer.write_span_label(mr.pattern.concept)
            self.writer.write_tag("span", close=True)

    def continue_doc_span(self, match_results: Sequence["MatchResult"]):
        """
        Continue a doc span

        Args:
          match_results: Sequence[MatchResult]: Match results for the doc span

        Returns:

        """
        if not match_results:
            return
        self.base_color = mix_hex_color_strings(
            list(self.writer.get_match_result_color(mr) for mr in match_results)
        )
        self.tooltip.extend(mr.pattern.concept for mr in match_results)

    def write_span_start(self):
        """Write tags to start a span"""
        if self.base_color is None and self.span_color is None:
            self.writer.write_tag("span")
            return
        if self.base_color and self.span_color:
            color = mix_hex_color_strings(self.base_color, self.span_color, t=0.7)
        elif self.base_color:
            color = self.base_color
        else:
            color = self.span_color
        self.writer.write_tag(
            "span",
            tag_args={
                "style": "background-color:" + color,
                "title": "; ".join(self.tooltip),
            },
        )

    def write_span_end(self):
        """Write tags to end a span"""
        self.writer.write_tag("span", close=True)

    def summarize_results(
        self,
        match_results: Sequence["MatchResult"],
        html_output: bool = False,
        max_num_concepts: int = 7,
    ) -> str:
        """
        Summarize a collection of match results

        Args:
          match_results: Sequence[MatchResult]: Match results to summarize
          html_output: bool: Whether to format as html (or text) (Default value = False)
          max_num_concepts: int: Maximum number of concepts to include (Default value = 7)

        Returns:
          HTML summarizes the match results
        """

        def decorate(concept: str) -> str:
            if html_output:
                color = self.writer.concept_colors.get(
                    concept, self.writer.default_span_color
                )
                return f'<u style="color: {color}">' + html.escape(concept) + "</u>"
            else:
                return concept

        concept_counter = Counter(mr.pattern.concept for mr in match_results)
        most_common = Counter(dict(concept_counter.most_common(max_num_concepts)))
        result = "; ".join(f"{decorate(k)}({v})" for k, v in most_common.items())
        # if most_common.total() < len(match_results):  # python 3.10
        if sum(most_common.values()) < len(match_results):
            result += f";... ; total({len(match_results)})"
        return result
