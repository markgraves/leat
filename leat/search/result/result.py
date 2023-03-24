""""Results of pattern matches"""

from abc import ABC
from collections import defaultdict, Counter
import re
from typing import Dict, Optional, Sequence, Union

from leat.store.core import Document
from ..pattern import MatchPattern


class BaseResult(ABC):
    "Base Results"

    pass


class DocResult(BaseResult):
    "Results of pattern matches in a document"

    def __init__(
        self,
        doc: Document,
        pat_results: Dict[MatchPattern, Sequence["MatchResult"]],
        section_sep: int = 0,
        section_max: int = 0,
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
        if section_sep or section_max:
            # print('DEBUG: Sectioning results', section_sep, section_max)
            self.section_results(section_sep, section_max)

    def section_results(self, section_sep: int = 125, section_max: int = 0):
        "Divide document into annotated sections separated by sect_sep or more"
        if self.sect_results is not None:
            return self.sect_results
        windows = self.__class__.bin_sliding_window(
            self.pat_results, section_sep, section_max=section_max
        )
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
        results,
        section_sep=125,
        sect_start_pad=20,
        sect_end_pad=35,
        section_max: int = 0,
    ):
        "Build a list of windows from with seperation of distance section_sep or more"
        span_start = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        # start: end: match_pattern: [matches]
        for k, vlist in results.items():
            for v in vlist:
                span_start[v.start][v.end][k].append(v)
        return __class__.bin_sliding_window_span(
            span_start, maxsep=section_sep, maxlength=section_max
        )

    @staticmethod
    def bin_sliding_window_span(
        span_keyed_dict, maxsep: int = 1, maxlength: Optional[int] = None
    ):
        "Build a list of windows from dict {start: end: key: spans} with separation of distance section_sep or more"
        last = -1
        start = 0
        results = []
        current = []
        for i in sorted(span_keyed_dict):
            if not current:
                start = i
            if last + maxsep < i:
                if current:
                    results.append(current)
                    current = []
                    start = i
            maxend = max(span_keyed_dict[i].keys())
            if maxlength and (maxend - start) > maxlength:
                mr1 = list(list(list(span_keyed_dict[i].values())[0].values())[0])[0]
                try:
                    name = mr1.doc.name
                except (AttributeError):
                    name = mr1
                if current:
                    results.append(current)
                    current = []
                    print(
                        "DEBUG",
                        "For %s, splitting span length %s greater than %s at %s"
                        % (name, maxend - start, maxlength, i),
                    )
                else:
                    print(
                        "INFO:",
                        "For %s, span length %s greater than %s at %s"
                        % (name, maxend - start, maxlength, i),
                    )
                    # print(mr1.doc.text[i:maxend])
                start = i
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
            sweepd[mr.start]["s"].append(mr)
            sweepd[mr.end]["e"].append(mr)
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

    def summarize_match_result_terms(
        self,
        concept_key: bool = False,
        counter_value: bool = True,
        counter_value_as_dict: bool = True,
        fold_case: bool = True,
    ):
        "Summarize a list of match results, returning as a dictionary keyed by match pattern"
        return summarize_match_result_terms(
            self.pat_results,
            concept_key=concept_key,
            counter_value=counter_value,
            counter_value_as_dict=counter_value_as_dict,
            fold_case=fold_case,
        )

    def astext(
        self, uppercase_match=False, start_pad=None, end_pad=None, include_labels=True
    ):
        if include_labels:
            rstr = str(self.doc.name)
            rstr += "\n"
        else:
            rstr = ""
        for sect_result in self.sect_results:
            rstr += sect_result.astext(
                start_pad=start_pad, end_pad=end_pad, include_labels=include_labels
            )
        return rstr

    def to_dict(self, include_text=False, compact_match_result=True):
        d = {}
        d["doc"] = self.doc.to_dict(include_text=include_text, use_hash=True)
        d["pat_results"] = [
            [
                k.to_dict(),
                [
                    v.to_dict(
                        include_doc=(not compact_match_result),
                        include_pattern=(not compact_match_result),
                    )
                    for v in vlist
                ],
            ]
            for k, vlist in self.pat_results.items()
        ]
        if hasattr(self, "section_sep"):
            d["section_sep"] = self.section_sep
        return d

    @classmethod
    def from_dict(cls, d):
        """Create a DocResult from a dict"""
        doc = Document.from_dict(d["doc"])
        pat_results_dict = d.get("pat_results", {})
        pat_results = {}
        for p_r in pat_results_dict:
            pat_obj = MatchPattern.from_dict(p_r[0])
            pat_results[pat_obj] = [
                MatchResult.from_dict(r, default_doc=doc, default_pattern=pat_obj)
                for r in p_r[1]
            ]
        section_sep = d.get("section_sep", 0)
        return cls(doc, pat_results, section_sep=section_sep)

    def __contains__(self, concept_or_match_pattern):
        """True iff doc result has a match pattern for the concept or match pattern"""
        if isinstance(concept_or_match_pattern, str):
            return concept_or_match_pattern in [
                pat.concept for pat in self.pat_results.keys()
            ]
        elif isinstance(concept_or_match_pattern, MatchPattern):
            return concept_or_match_pattern in self.pat_results
        else:
            return False


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
        return max(0, min(r.start for r in self.results) - pad)

    def end(self, pad=None):
        pad = pad if pad is not None else self.end_pad
        return min(len(self.doc.text), max(r.end for r in self.results) + pad)

    def summarize_match_result_terms(
        self,
        concept_key: bool = False,
        counter_value: bool = True,
        counter_value_as_dict: bool = True,
        fold_case: bool = True,
    ):
        "Summarize a list of match results, returning as a dictionary keyed by match pattern"
        return summarize_match_result_terms(
            self.results,
            concept_key=concept_key,
            counter_value=counter_value,
            counter_value_as_dict=counter_value_as_dict,
            fold_case=fold_case,
        )

    def astext(
        self, uppercase_match=False, start_pad=None, end_pad=None, include_labels=True
    ):
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
        if not include_labels:
            rstr += "\n"
            return rstr
        for mr in self.results:
            mrtext = mr.astext(
                uppercase_match=uppercase_match, include_labels=include_labels
            )
            rstr += "\n" + " " * (mr.start - start) + mrtext
        rstr += "\n"
        return rstr


class MatchResult(BaseResult):
    "Result of pattern match in a document"

    def __init__(self, doc: Document, pattern: MatchPattern, match: re.Match):
        self.match = match
        self.start = match.start()
        self.end = match.end()
        self.match_text = match.group(0)
        self.pattern = pattern
        self.doc = doc

    def astext(self, uppercase_match=False, include_labels=True):
        "Text string for match"
        text = self.match_text
        if uppercase_match:
            text = text.upper()
        return text + f"[{self.pattern.concept}]" if include_labels else text

    def to_dict(self, include_doc=True, include_pattern=True):
        d = {}
        d["start"] = self.start
        d["end"] = self.end
        d["match_text"] = self.match_text
        if include_pattern:
            d["pattern"] = self.pattern.to_dict()
        if include_doc:
            d["doc"] = self.doc.to_dict()
        return d

    @classmethod
    def from_dict(cls, d, default_pattern=None, default_doc=None):
        """Create a MatchResult from a dict"""
        obj = cls.__new__(cls)
        super(MatchResult, obj).__init__()
        obj.match = None
        obj.start = d["start"]
        obj.end = d["end"]
        obj.match_text = d["match_text"]
        pattern = d.get("pattern")
        if pattern is not None:
            obj.pattern = MatchPattern.from_dict(pattern)
        elif default_pattern is not None:
            obj.pattern = default_pattern
        else:
            obj.pattern = None
        doc = d.get("doc")
        if doc is not None:
            obj.doc = Document.from_dict(doc)
        elif default_doc is not None:
            obj.doc = default_doc
        else:
            obj.doc = None
        return obj

    def __str__(self):
        return f"<{__class__.__name__} {(self.start, self.end)} {self.astext()}>"


def summarize_match_result_terms(
    match_results: Union[list, dict],
    concept_key: bool = False,
    counter_value: bool = True,
    counter_value_as_dict: bool = True,
    fold_case: bool = True,
):
    "Summarize a list of match results, returning as a dictionary keyed by match pattern"
    if counter_value:
        results = defaultdict(Counter)
    else:
        results = defaultdict(list)
    if isinstance(match_results, dict):
        for pat, mr_list in match_results.items():
            for mr in mr_list:
                # print('DEBUG', 'MR', (mr.pattern.pattern, mr.match.group(0), mr.start(), mr.end()))
                if counter_value:
                    results[pat][mr.match.group(0)] += 1
                else:
                    results[pat].append(mr.match.group(0))
    else:
        for mr in match_results:
            # print('DEBUG', 'MR', (mr.pattern.pattern, mr.match.group(0), mr.start(), mr.end()))
            if counter_value:
                results[mr.pattern][mr.match.group(0)] += 1
            else:
                results[mr.pattern].append(mr.match.group(0))
    # Maybe fold case
    if fold_case and counter_value:
        newresults = {}
        for pat, ctr in results.items():
            if not (pat.flags & re.IGNORECASE):
                # only fold case if the pattern had ignore case flag set (i.e, was case insensitive)
                newresults[pat] = ctr
                continue
            equivalent_terms = defaultdict(list)
            for term in ctr:
                equivalent_terms[term.casefold()].append(term)
            folded_terms = {}
            for lower, term_list in equivalent_terms.items():
                if len(term_list) == 1:
                    continue
                key = max(
                    term_list
                )  # max takes the highest ord value, so prefer lower case or accented
                for term in term_list:
                    if term != key:
                        folded_terms[term] = key
            newctr = Counter()
            for term, val in ctr.items():
                newctr[folded_terms.get(term, term)] += val
            newresults[pat] = newctr
        results = newresults
    # Return results
    if concept_key:
        # First, merge multiple patterns for same concept
        newresults = {}
        for pat, ctr in results.items():
            if pat.concept in newresults:
                newresults[pat.concept].update(ctr)
            else:
                newresults[pat.concept] = ctr
        if counter_value and counter_value_as_dict:
            return {
                concept: dict(ctr.most_common(None))
                for concept, ctr in newresults.items()
            }
        else:
            return newresults
    else:
        if counter_value and counter_value_as_dict:
            return {
                pattern: dict(ctr.most_common(None)) for pattern, ctr in results.items()
            }
        else:
            return results
