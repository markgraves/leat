""""Results of pattern matches"""

from abc import ABC
from collections import defaultdict
import re
from typing import Dict, Optional, Sequence, Union

from ...store.core import Document
from ..pattern import MatchPattern


class BaseResult(ABC):
    "Base Results"

    pass


class DocResult(BaseResult):
    "Results of pattern matches in a document"

    def __init__(
        self,
        doc: Document,
        pat_results: Dict[MatchPattern, Sequence[Union["MatchResult", re.Match]]],
        section_sep: int = 0,
    ):
        self.doc = doc
        clean_results = {
            p: [
                r if type(r) == MatchResult else MatchResult(doc, p, r) for r in results
            ]
            for p, results in pat_results.items()
        }
        self.pat_results = clean_results
        self.sect_results: Optional[Sequence["DocSectResult"]] = None
        if section_sep:
            self.section_results(section_sep)

    def section_results(self, section_sep: int = 125):
        "Divide document into annotated sections separated by sect_sep or more"
        if self.sect_results is not None:
            return self.sect_results
        windows = self.__class__.bin_sliding_window(self.pat_results, section_sep)
        self.sect_results = [DocSectResult(self.doc, w) for w in windows]

    def all_results(self, pat=None, concept=""):
        if pat:
            return self.pat_results[pat]
        elif concept:
            return sum(
                [
                    vlist
                    for k, vlist in self.pat_results.items()
                    if k.concept == concept
                ],
                [],
            )
        else:
            return sum(self.pat_results.values(), [])

    @staticmethod
    def bin_sliding_window(
        results, section_sep=125, sect_start_pad=20, sect_end_pad=35
    ):
        "Build a list of windows from with seperation of distance section_sep or more"
        span_start = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        # start: end: match_pattern: [matches]
        for k, vlist in results.items():
            for v in vlist:
                span_start[v.start()][v.end()][k].append(v)
        return __class__.bin_sliding_window_span(span_start, section_sep)

    @staticmethod
    def bin_sliding_window_span(span_keyed_dict, maxsep=1):
        "Build a list of windows from dict {start: end: key: spans} with seperation of distance section_sep or more"
        last = -1
        results = []
        current = []
        for i in sorted(span_keyed_dict):
            if last + maxsep < i:
                if current:
                    results.append(current)
                    current = []
            maxend = max(span_keyed_dict[i].keys())
            # current[(i, maxend)] = int_keyed_dict[i]
            current.extend(
                v
                for pat_match in span_keyed_dict[i].values()
                for k, vlist in pat_match.items()
                for v in vlist
            )
            last = max(last, maxend)
        if current:
            results.append(current)
        return results

    @staticmethod
    def line_sweep_spans(match_results):
        """
        Calclulates sweep spans for list of match results
        return {index: {'s|e|c': [match_pattern, ...]}}
        with Start, End, Continue list for each index
        Note: index for end is pythonic, so index after the matched string ends
        """
        # sweepd = {index: {'s|e|c': [match_pattern, ...]}}
        sweepd = defaultdict(lambda: defaultdict(list))
        for mr in match_results:
            sweepd[mr.start()]["s"].append(mr)
            sweepd[mr.end()]["e"].append(mr)
        sweepd = dict(sorted(sweepd.items()))
        current = []
        newd = {}
        for indx, d in sweepd.items():
            if "e" in d:
                current = [mr for mr in current if mr not in d["e"]]
            if current:
                d["c"] = current.copy()
            if "s" in d:
                current.extend(d["s"])
            newd[indx] = dict(d)
        return newd

    def astext(self, uppercase_match=False, start_pad=None, end_pad=None):
        rstr = str(self.doc.name)
        rstr += "\n"
        for sect_result in self.sect_results:
            rstr += sect_result.astext(start_pad=start_pad, end_pad=end_pad)
        return rstr


class DocSectResult(BaseResult):
    "Results of pattern matches in a document section"

    def __init__(
        self,
        doc: Document,
        results: "Sequence[MatchResult]",
        start_pad: Optional[int] = 0,
        end_pad: Optional[int] = 0,
    ):
        self.doc = doc
        self.results = results
        self.start_pad = start_pad
        self.end_pad = end_pad

    def start(self, pad=None):
        pad = pad if pad is not None else self.start_pad
        return max(0, min(r.start() for r in self.results) - pad)

    def end(self, pad=None):
        pad = pad if pad is not None else self.end_pad
        return min(len(self.doc.text), max(r.end() for r in self.results) + pad)

    def astext(self, uppercase_match=False, start_pad=None, end_pad=None):
        "Text string for section with matches"
        start_pad = start_pad if start_pad is not None else self.start_pad
        end_pad = end_pad if end_pad is not None else self.end_pad
        start = self.start(pad=start_pad)
        end = self.end(pad=end_pad)
        rstr = (
            self.doc.text[start:end]
            .replace("\n", " ")
            .replace("\r", " ")
            .replace("\f", " ")
            .replace("\t", " ")
        )
        for mr in self.results:
            mrtext = mr.astext(uppercase_match=uppercase_match)
            rstr += "\n" + " " * (mr.start() - start) + mrtext
        rstr += "\n"
        return rstr


class MatchResult(BaseResult):
    "Result of pattern match in a document"

    def __init__(self, doc: Document, pattern: MatchPattern, match: re.Match):
        self.match = match
        self.pattern = pattern
        self.doc = doc

    def start(self):
        return self.match.start()

    def end(self):
        return self.match.end()

    def astext(self, uppercase_match=False):
        "Text string for match"
        text = self.doc.text[self.match.start() : self.match.end()]
        assert text == self.match.group(0)
        if uppercase_match:
            text = text.upper()
        return text + f"[{self.pattern.concept}]"

    def __str__(self):
        return f"<{__class__.__name__} {(self.start(), self.end())} {self.astext()}>"