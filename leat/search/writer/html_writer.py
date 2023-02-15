"""Base Writer to write document results as HTML"""

import html
from io import IOBase, StringIO
from pathlib import Path
from typing import Optional, Union

from . import BaseWriter, SpanScheme
from ..result import DocResult, DocSectResult, MatchResult

DEFAULT_SPAN_COLOR = "#F1E740"  # dark yellow


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
        self.pretty_html = self.scheme.get("pretty_html", True)  # True for debugging
        self.concept_colors = self.scheme.get("concept_colors", {})
        self.default_span_color = DEFAULT_SPAN_COLOR

    def write_doc_result(self, item: DocResult):
        "Write document result"
        self.write(str(item.doc.name))
        self.write_line()
        for sect_result in item.sect_results:
            self.write_doc_section_result(sect_result)

    def write_doc_section_result(self, item: DocSectResult):
        "Write document section result"

        def get_match_result_color(match_result):
            "Return the color for a match result concept"
            return self.concept_colors.get(
                match_result.pattern.concept, self.default_span_color
            )

        start = item.start(pad=self.start_pad)
        end = item.end(pad=self.end_pad)
        # Sweep spans
        sweepd = DocResult.line_sweep_spans(item.results)
        self.write_tag("div", newline=True)
        self.write_tag("span")
        current_index = start
        # span_stack = []
        for indx, d in sweepd.items():
            tooltip = []
            if "c" in d:
                base_color = mix_hex_color_strings(
                    list(get_match_result_color(mr) for mr in d["c"])
                )
                tooltip.extend(mr.pattern.concept for mr in d["c"])
            else:
                base_color = None
            self.write_clean_text(item.doc.text[current_index:indx])
            self.write_tag("span", close=True, newline=True)
            for mr in d.get("e", []):
                self.write_tag(
                    "span",
                    tag_args={
                        "style": "color:" + get_match_result_color(mr),
                        "title": mr.astext(),
                    },
                )
                self.write_span_label(mr.pattern.concept)
                self.write_tag("span", close=True)
            if "s" in d:
                span_color = mix_hex_color_strings(
                    list(get_match_result_color(mr) for mr in d.get("s", []))
                )
                tooltip.extend(mr.pattern.concept for mr in d["s"])
            else:
                span_color = None
            if base_color is not None or span_color is not None:
                if base_color and span_color:

                    color = mix_hex_color_strings(base_color, span_color, t=0.7)
                elif base_color:
                    color = base_color
                elif span_color:
                    color = span_color
                else:
                    print("INTERNAL ERROR")
                self.write_tag(
                    "span",
                    tag_args={"style": "color:" + color, "title": "; ".join(tooltip)},
                )
            else:
                self.write_tag("span")
            current_index = indx
        self.write_clean_text(item.doc.text[current_index:end])
        self.write_tag("span", close=True)
        self.write_tag("div", close=True, newline=True)

    def write_span_label(self, text: str):
        "Write span label"
        self.write(f"<sup>[{html.escape(text)}]</sup>")

    def write_clean_text(self, text: str):
        "Clean and write text"
        if self.pretty_html:
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


def mix_hex_color_strings(color_a, color_b=None, t=0.5, gamma=2):
    "Mix two hex colors"
    # See https://stackoverflow.com/questions/726549/algorithm-for-additive-color-mixing-for-rgb-values
    def hex_to_float(h):
        """Convert a hex rgb string (e.g. #ffffff) to an RGB tuple (float, float, float)."""
        return tuple(int(h[i : i + 2], 16) / 255.0 for i in (1, 3, 5))  # skip '#'

    def float_to_hex(rgb):
        """Convert an RGB tuple or list to a hex RGB string."""
        return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"

    if color_b is None:
        assert not isinstance(color_a, str)
        if len(color_a) == 1:
            return color_a[0]
        floats = [hex_to_float(h) for h in color_a]
        rgb = [
            pow(sum((1 / len(floats)) * c[i] ** gamma for c in floats), 1 / gamma)
            for i in (0, 1, 2)
        ]
        # print(color_a, floats, rgb)
    else:
        a = hex_to_float(color_a)
        b = hex_to_float(color_b)
        rgb = [
            pow((1 - t) * a[i] ** gamma + t * b[i] ** gamma, 1 / gamma)
            for i in (0, 1, 2)
        ]
    return float_to_hex(rgb)
