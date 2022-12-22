"""Base Writer to write document results as HTML"""

import html
from io import IOBase, StringIO
from pathlib import Path
from typing import Optional, Union

from . import BaseWriter, SpanScheme
from ..result import DocResult, DocSectResult, MatchResult

class HTMLWriter(BaseWriter):
    "Base Reader to write document results as html"

    def __init__(self, stream: Optional[IOBase] = None, scheme=None, start_pad=None, end_pad=None):
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
            print('WARN:', 'Ignoring unknown scheme type for HTMLWriter: ', scheme)
            self.scheme = SpanScheme(start_pad=start_pad, end_pad=end_pad)
        self.start_pad = start_pad if start_pad is not None else self.scheme.start_pad
        self.end_pad = end_pad if start_pad is not None else self.scheme.end_pad
        self.pretty_html = self.scheme.get('pretty_html', True)  # True for debugging
        self.concept_colors = self.scheme.get('concept_colors', {})
        self.default_span_color = '#FFFF00'
    

    def write_doc_result(self, item: DocResult):
        "Write document result"
        self.write(str(item.doc.name))
        self.write_line()
        for sect_result in item.sect_results:
            self.write_doc_section_result(sect_result)
        
        
    def write_doc_section_result(self, item: DocSectResult):
        "Write document section result"
        start = item.start(pad=self.start_pad)
        end = item.end(pad=self.end_pad)
        # Sweep spans
        sweepd = DocResult.line_sweep_spans(item.results)
        self.write_tag('div', newline=True)
        current_index = start
        for indx, d in sweepd.items():
            if 'c' in d:
                print('WARN:', 'HTMLWriter does not yet handle overlapping spans')
            self.write_clean_text(item.doc.text[current_index:indx])
            for mr in d.get('e', []):
                self.write_span_label(mr.pattern.concept)
                self.write_tag('span', close=True)
            for mr in d.get('s', []):
                self.write_tag('span', tag_args={'style': 'color:' + self.concept_colors.get(mr.pattern.concept, self.default_span_color)})
            current_index = indx
        self.write_clean_text(item.doc.text[current_index:end])
        self.write_tag("div", close=True, newline=True)

    def write_span_label(self, text: str):
        "Write span label"
        self.write(f'<sup>[{html.escape(text)}]</sup>')

    def write_clean_text(self, text: str):
        "Clean and write text"
        if self.pretty_html:
            text = (text.replace("\n", " ")
            .replace("\r", " ")
            .replace("\f", " ")
            .replace("\t", " ")
                    )
        self.write(html.escape(text))

    def write_tag(self, name: str, tag_args={}, close=False, singleton=False, newline=False):
        "Write html tag"
        arg_string = ' ' + ' '.join(k + '=' + f'"{v}"' for k, v in tag_args.items()) if tag_args else ''
        self.stream.write(
            '<' + ('/' if close else '') + name + arg_string + ('/' if singleton else '') + '>'
            + ('\n' if newline else '')
        )
       
    def write_line(self, text: Optional[str] = None):
        "Write line"
        if text is not None:
            self.stream.write(text)
        self.stream.write('\n')

    def write(self, text: str):
        "Write text"
        self.stream.write(text)
