"""Delegate writer code for match result"""

from abc import ABC
from collections import Counter
import html

from .colors import mix_hex_color_strings


class BaseWriterDelegate(ABC):
    "Base Writer Delegate"

    def start_section(self):
        pass

    def end_section(self):
        pass

    def init_span(self):
        pass

    def start_doc_span(self, match_results):
        pass

    def end_doc_span(self, match_results):
        pass

    def continue_doc_span(self, match_results):
        pass

    def write_span_start(self):
        pass

    def write_span_end(self):
        pass


class HTMLInlineSpanDelegate(BaseWriterDelegate):
    "Delegates writing inline html spans for match result"

    def __init__(self, writer):
        self.writer = writer
        wopts = self.writer.writer_options
        self.details_summary = wopts.get("details_summary", True)
        if self.details_summary:
            self.collapse_section = wopts.get("collapse_section", True)
            self.collapse_section_default_open = wopts.get(
                "collapse_section_default_open", True
            )
            self.collapse_document = wopts.get("collapse_document", True)
            self.tag_args_document_details = {
                "style": "margin-left: 2em;",
                **wopts.get("tag_args_document_details", {}),
            }
            self.tag_args_document_summary = {
                "style": "margin-left: -2em;",
                **wopts.get("tag_args_document_summary", {}),
            }
        else:
            self.collapse_section = False
            self.collapse_document = False

    def start_doc(self, name, match_results=None, html_output=True):
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
        if self.collapse_document:
            self.writer.write_tag("details", close=True)
        self.writer.write_tag("div", close=True, newline=True)

    def start_section(self, match_results=None):
        "Write tags to start section, and maybe summarize match_results"
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
        self.writer.write_tag("span", close=True)
        if self.collapse_section:
            self.writer.write_tag("details", close=True)
        self.writer.write_tag("div", close=True, newline=True)

    def init_span(self):
        self.tooltip = []
        self.base_color = None
        self.span_color = None

    def start_doc_span(self, match_results):
        if not match_results:
            return
        self.span_color = mix_hex_color_strings(
            list(self.writer.get_match_result_color(mr) for mr in match_results)
        )
        self.tooltip.extend(mr.pattern.concept for mr in match_results)

    def end_doc_span(self, match_results):
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

    def continue_doc_span(self, match_results):
        if not match_results:
            return
        self.base_color = mix_hex_color_strings(
            list(self.writer.get_match_result_color(mr) for mr in match_results)
        )
        self.tooltip.extend(mr.pattern.concept for mr in match_results)

    def write_span_start(self):
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
        self.writer.write_tag("span", close=True)

    def summarize_results(
        self, match_results, html_output=False, max_num_concepts=7
    ) -> str:
        "Summarize a collection of match results"

        def decorate(concept):
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
