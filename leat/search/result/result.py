""""Results of pattern matches"""

from abc import ABC
from collections import defaultdict, Counter
import re
from typing import Dict, List, Optional, Sequence, Union

from leat.store.core import Document
from ..pattern import MatchPattern


class BaseResult(ABC):
    """Base class for pattern match results"""

    pass


class DocResult(BaseResult):
    """Results of pattern matches in a document

    Attributes:
      doc: Document: The document searched
      pat_results: Dict[MatchPattern: Sequence[MatchResult]]: Dictionary of match pattern and the results found that matched
      sect_results: Sequence[DocSectResult] | None: Sections of the document with their results, if created
    """

    def __init__(
        self,
        doc: Document,
        pat_results: Dict[MatchPattern, Sequence["MatchResult"]],
        section_sep: int = 0,
        section_max: int = 0,
    ):
        """
        Create a DocResult object that contains the result of pattern matches in a document

        Args:
          doc: Document: The document searched
          pat_results: Dict[MatchPattern: Sequence[MatchResult]]: Dictionary of match pattern and the results found that matched
          section_sep: int: Length of text without patterns that is sufficient to create a new section or results (Default value = 0)
          section_max: int: Maximum length of a section. Useful if downstream data structures have a max length, e.g., deep learning tensors. Ignore if 0. (Default value = 0)

        Returns:
           DocResult: A document result object
        """
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

    def section_results(
        self, section_sep: int = 125, section_max: int = 0
    ) -> Sequence["DocSectResult"]:
        """
        Divide document into annotated sections separated by sect_sep or more

        Args:
          section_sep: int: Length of match-less text sufficient to start a new section (Default value = 125)
          section_max: int: Maximum length of a section. (Default value = 0)

        Returns:
          List[DocSectResult]: List of results divided into document section
        """
        if self.sect_results is not None:
            return self.sect_results
        windows = self.__class__.bin_sliding_window(
            self.pat_results, section_sep, section_max=section_max
        )
        self.sect_results = [DocSectResult(self.doc, w) for w in windows]

    def all_results(
        self, pat: Optional[MatchPattern] = None, concept: str = ""
    ) -> Sequence["MatchResult"]:
        """
        Returns list of all match results, with possible filtering

        Args:
          pat: MatchPattern | None: If given, only return matches for the match pattern (Default value = None)
          concept: str: If given, only return matches for the concept (Default value = "")

        Returns:
          List[MatchResult]: List of all match results
        """
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
        results: Dict[MatchPattern, Sequence["MatchResult"]],
        section_sep: int = 125,
        sect_start_pad: int = 20,
        sect_end_pad: int = 35,
        section_max: int = 0,
    ) -> list:
        """
        Build a list of windows from with separation of distance section_sep or more

        Args:
          results: Dict[MatchPattern: Sequence[MatchResult]]: Dictionary of match pattern and the results found that matched
          section_sep: int: Length of match-less text sufficient to start a new section (Default value = 125)
          sect_start_pad: int: Number of characters to include prior to match (Default value = 20)
          sect_end_pad: int: Number of characters to include after the match  (Default value = 35)
          section_max: int: Maximum length of a section. (Ignore if 0) (Default value = 0)

        Returns:
          list: List of windows with matches
        """
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
        span_keyed_dict: dict, maxsep: int = 1, maxlength: Optional[int] = None
    ) -> List[dict]:
        """
        Build a list of windows from dict {start: end: key: spans} with separation of distance section_sep or more

        Args:
          span_keyed_dict: dict: Format is start: end: match_pattern: [matches]
          maxsep: int: Length of match-less text sufficient to start a new section (Default value = 1)
          maxlength: Optional[int]: Maximum length of a section. Ignore if 0 or None. (Default value = None)

        Returns:
          List(dict): List of span keyed dict divided into sections
        """
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
    def line_sweep_spans(match_results: Sequence["MatchResult"]) -> dict:
        """
        Calclulates sweep spans for list of match results

        Args:
          match_results: Sequence[MatchResult]:  Match results to process

        Returns:
          dict: Format is {index: {'s|e|c': [match_pattern, ...]}} with Start, End, Continue list for each index

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
    ) -> dict:
        """
        Summarize a list of match results, returning as a dictionary keyed by match pattern

        Args:
          concept_key: bool: Whether to key by just the concept (Default value = False)
          counter_value: bool: If True, returned dictionary for each pattern should be a Counter (Default value = True)
          counter_value_as_dict: bool: Cast the returned Counter as a python dict (Default value = True)
          fold_case: bool: Fold upper into lower case while matching terms for Counter creation (Default value = True)

        Returns:
          dict: Result terms counter, keyed by match pattern (or concept)
        """
        return summarize_match_result_terms(
            self.pat_results,
            concept_key=concept_key,
            counter_value=counter_value,
            counter_value_as_dict=counter_value_as_dict,
            fold_case=fold_case,
        )

    def astext(
        self,
        uppercase_match: bool = False,
        start_pad: Optional[int] = None,
        end_pad: Optional[int] = None,
        include_labels: bool = True,
    ) -> str:
        """
        Format the document results as a text

        Args:
          uppercase_match: bool: If True, uppercase the matching text (Default value = False)
          start_pad:Optional[int]: Number of characters to include prior to match (Default value = None)
          end_pad:Optional[int]: Number of characters to include after the match (Default value = None)
          include_labels:bool: Whether to include concept labels in resulting text (Default value = True)

        Returns:
          Text of document result (spans of text)
        """
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

    def to_dict(
        self, include_text: bool = False, compact_match_result: bool = True
    ) -> dict:
        """
        Convert Document Result to a dict (for serialization)

        Args:
          include_text: bool: Whether to include document text (Default value = False)
          compact_match_result:bool: Whether to compact the match result to save space, by removing redundancies (Default value = True)

        Returns:
          dict: Dictionary representation of object instance
        """
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
    def from_dict(cls, d: dict):
        """
        Create a DocResult from a dict

        Args:
          d: dict: Dictionary of object

        Returns:
          DocResult: Created from the dictionary
        """
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

    def __contains__(self, concept_or_match_pattern) -> bool:
        """
        True iff doc result has a match pattern for the concept or match pattern

        Args:
          concept_or_match_pattern:

        Returns:
          bool: True iff doc result has a match pattern for the concept or match pattern
        """
        if isinstance(concept_or_match_pattern, str):
            return concept_or_match_pattern in [
                pat.concept for pat in self.pat_results.keys()
            ]
        elif isinstance(concept_or_match_pattern, MatchPattern):
            return concept_or_match_pattern in self.pat_results
        else:
            return False


class DocSectResult(BaseResult):
    """Results of pattern matches in a document section

    Attributes:
      doc: Document: The document searched
      results: Dict[MatchPattern: Sequence[MatchResult]]: Dictionary of match pattern and the results found that match
      start_pad: int | None: Number of characters to include prior to match
      end_pad: int | None:  Number of characters to include after the match
    """

    def __init__(
        self,
        doc: Document,
        results: "Sequence[MatchResult]",
        start_pad: Optional[int] = 0,
        end_pad: Optional[int] = 0,
    ):
        """
        Create a container for the match patterns in a section of a document

        Args:
          doc: Document: The document searched
          results: Dict[MatchPattern: Sequence[MatchResult]]: Dictionary of match pattern and the results found that matched
          start_pad: int | None: Number of characters to include prior to match (Default value = 0)
          end_pad: int | None:  Number of characters to include after the match (Default value = 0)
        """
        self.doc = doc
        self.results = results
        self.start_pad = start_pad
        self.end_pad = end_pad

    def start(self, pad: Optional[int] = None) -> int:
        """
        Start position for the section

        Args:
          pad: Optional[int]: Number of characters to include prior to the first match. If None, use instance default (Default value = None)

        Returns:
          int: Start position for the section
        """
        pad = pad if pad is not None else self.start_pad
        return max(0, min(r.start for r in self.results) - pad)

    def end(self, pad: Optional[int] = None) -> int:
        """
        End position for the section

        Args:
          pad: Optional[int]: Number of characters to include after the last match. If None, use instance default (Default value = None)

        Returns:
          int: End position for the section
        """
        pad = pad if pad is not None else self.end_pad
        return min(len(self.doc.text), max(r.end for r in self.results) + pad)

    def summarize_match_result_terms(
        self,
        concept_key: bool = False,
        counter_value: bool = True,
        counter_value_as_dict: bool = True,
        fold_case: bool = True,
    ) -> dict:
        """
        Summarize a list of match results, returning as a dictionary keyed by match pattern

        Args:
          concept_key: bool: Whether to key by just the concept (Default value = False)
          counter_value: bool: If True, returned dictionary for each pattern should be a Counter (Default value = True)
          counter_value_as_dict: bool: Cast the returned Counter as a python dict (Default value = True)
          fold_case: bool: Fold upper into lower case while matching terms for Counter creation (Default value = True)

        Returns:
          dict: Match results counter, keyed by match pattern (or concept)
        """
        return summarize_match_result_terms(
            self.results,
            concept_key=concept_key,
            counter_value=counter_value,
            counter_value_as_dict=counter_value_as_dict,
            fold_case=fold_case,
        )

    def astext(
        self,
        uppercase_match: bool = False,
        start_pad: Optional[int] = None,
        end_pad: Optional[int] = None,
        include_labels: bool = True,
    ) -> str:
        """
        Text string for section with matches

        Args:
          uppercase_match:bool: If True, uppercase the matching text (Default value = False)
          start_pad: Optional[int]:Number of characters to include prior to match (Default value = None)
          end_pad: Optional[int]: Number of characters to include after the match (Default value = None)
          include_labels:bool: Whether to include concept labels in resulting text (Default value = True)

        Returns:
          str: Text of document result (spans of text)
        """
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
    """Result of pattern match in a document

    Attributes:
      doc: Document: The document searched
      pattern: MatchPattern: The pattern found in the search
      match: re.Match: The match object from the search
      start: int: The beginning of the match (from the match object)
      end: int: The end of the match (from the match object)
      match_text: str: The matched text (from the match object)
    """

    def __init__(self, doc: Document, pattern: MatchPattern, match: re.Match):
        """
        The result of a match within a document

        Args:
          doc: Document: The document searched
          pattern: MatchPattern: The pattern found in the search
          match: re.Match: The match object from the search
        """
        self.match = match
        self.start: int = match.start()
        self.end: int = match.end()
        self.match_text: str = match.group(0)
        self.pattern = pattern
        self.doc = doc

    def astext(self, uppercase_match: bool = False, include_labels: bool = True) -> str:
        """
        Text string for match

        Args:
          uppercase_match:bool: If True, uppercase the matching text (Default value = False)
          include_labels:bool: Whether to include concept labels in resulting text (Default value = True)

        Returns:
          str: String of the match, possibly uppercased or with the concept label
        """
        text = self.match_text
        if uppercase_match:
            text = text.upper()
        return text + f"[{self.pattern.concept}]" if include_labels else text

    def to_dict(self, include_doc: bool = True, include_pattern: bool = True) -> dict:
        """
        Convert Match Result to a dict (for serialization)

        Args:
          include_doc: bool: Whether to include document (Default value = True)
          include_pattern: bool: Whether to include pattern (Default value = True)

        Note: The re.Match result is not included

        Returns:
          dict: Dictionary representation of object instance
        """
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
    def from_dict(
        cls,
        d: dict,
        default_pattern: Optional[MatchPattern] = None,
        default_doc: Optional[Document] = None,
    ) -> "MatchResult":
        """
        Create a MatchResult from a dict

        Args:
          d: dict: Dictionary of object
          default_pattern: Optional[MatchPattern]: Default MatchPattern to use in object creation if dict value for pattern is None (Default value = None)
          default_doc: Optional[Document]: Default Document to use in object creation if dict value for doc is None (Default value = None)

        Returns:
          MatchResult: Created from the dictionary
        """
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
        """ """
        return f"<{__class__.__name__} {(self.start, self.end)} {self.astext()}>"


def summarize_match_result_terms(
    match_results: Union[list, dict],
    concept_key: bool = False,
    counter_value: bool = True,
    counter_value_as_dict: bool = True,
    fold_case: bool = True,
) -> dict:
    """
    Summarize a list of match results, returning as a dictionary keyed by match pattern.

    Note: Function is used by both DocResult and DocSectResult to do the work of summarizing
          a list of match results, but could be used independently if desired

    Args:
      match_results: list | dict: List of match results, or dict keyed by match pattern with match results
      concept_key: bool: Whether to key summary by just the concept rather than the MatchPattern (Default value = False)
      counter_value: bool: If True, returned dictionary for each pattern should be a Counter (Default value = True)
      counter_value_as_dict: bool: Cast the returned Counter as a python dict (Default value = True)
      fold_case: bool: Fold upper into lower case while matching terms for Counter creation, unless match pattern was case sensitive (Default value = True)

    Returns:
      dict: Result terms counter, keyed by match pattern (or concept)
    """
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
