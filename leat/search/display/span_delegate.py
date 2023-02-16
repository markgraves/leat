"""Delegate writer code for match result"""

from abc import ABC

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

    def start_section(self):
        self.writer.write_tag("div", newline=True)
        self.writer.write_tag("span")

    def end_section(self):
        self.writer.write_tag("span", close=True)
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
