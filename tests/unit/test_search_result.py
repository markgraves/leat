from collections import Counter
import re

import pytest

from leat.store.core import Document
from leat.search.result import DocResult
from leat.search.result.result import summarize_match_result_terms


def test_bin_sliding_window_span_empty():
    assert DocResult.bin_sliding_window_span({}) == []


def test_bin_sliding_window_span():
    assert DocResult.bin_sliding_window_span({1: {3: {"a": ["x", "y"]}}}) == [
        ["x", "y"]
    ]
    assert DocResult.bin_sliding_window_span(
        {1: {3: {"a": ["x", "y"]}}, 5: {7: {"a": ["w"]}}}
    ) == [["x", "y"], ["w"]]
    assert DocResult.bin_sliding_window_span(
        {1: {3: {"a": ["x", "y"]}}, 4: {7: {"a": ["w"]}}}
    ) == [["x", "y", "w"]]


def test_bin_sliding_window_span_max_sep():
    assert DocResult.bin_sliding_window_span(
        {1: {3: {"a": ["x", "y"]}}, 4: {7: {"a": ["w"]}}}, maxlength=3
    ) == [["x", "y"], ["w"]]
    assert DocResult.bin_sliding_window_span(
        {1: {3: {"a": ["x", "y"]}}, 4: {7: {"a": ["w"]}}}
    ) == [["x", "y", "w"]]


## sweep spans

PARENS_RE = r"\(.*?\)"
BRACKETS_RE = r"\[.*?\]"
BRACES_RE = r"\{.*?\}"
MATCH_PATTERN = r"(?=(" + "|".join([PARENS_RE, BRACKETS_RE, BRACES_RE]) + r"))"


class M:
    def __init__(self, matched_text):
        self.matched_text = matched_text

    def group(self, *args):
        return self.matched_text


class MP:
    def __init__(self, pattern, flags=0):
        self.pattern = pattern
        self.flags = flags
        self.concept = "Test"


class MR:
    def __init__(self, pattern, matched_text, start, end, doc_text=""):
        self.doc_text = doc_text
        self.pattern = pattern
        self.matched_text = matched_text
        self.match = M(matched_text)
        self.start = start
        self.end = end

    def astext(self):
        return self.matched_text

    def __repr__(self):
        return f'MR("{self.pattern}", "{self.astext()}", {self.start}, {self.end})'

    def __eq__(self, other):
        return (
            self.start == other.start
            and self.end == other.end
            and self.pattern == other.pattern
            and self.astext() == other.astext()
        )


def gen_matches(text, pat):
    return [
        MR(m[1][0], m[1], m.start(1), m.end(1), text)
        for m in re.compile(pat).finditer(text)
    ]


SWEEP_SPANS_RESULTS = [
    ("", {}),
    ("()", {0: {"s": [MR("(", "()", 0, 2)]}, 2: {"e": [MR("(", "()", 0, 2)]}}),
    (
        "([])",
        {
            0: {"s": [MR("(", "([])", 0, 4)]},
            1: {"s": [MR("[", "[]", 1, 3)], "c": [MR("(", "([])", 0, 4)]},
            3: {"e": [MR("[", "[]", 1, 3)], "c": [MR("(", "([])", 0, 4)]},
            4: {"e": [MR("(", "([])", 0, 4)]},
        },
    ),
    (
        "([)]",
        {
            0: {"s": [MR("(", "([)", 0, 3)]},
            1: {"s": [MR("[", "[)]", 1, 4)], "c": [MR("(", "([)", 0, 3)]},
            3: {"e": [MR("(", "([)", 0, 3)], "c": [MR("[", "[)]", 1, 4)]},
            4: {"e": [MR("[", "[)]", 1, 4)]},
        },
    ),
    (
        "(12[4)56]{}",
        {
            0: {"s": [MR("(", "(12[4)", 0, 6)]},
            3: {"s": [MR("[", "[4)56]", 3, 9)], "c": [MR("(", "(12[4)", 0, 6)]},
            6: {"e": [MR("(", "(12[4)", 0, 6)], "c": [MR("[", "[4)56]", 3, 9)]},
            9: {"e": [MR("[", "[4)56]", 3, 9)], "s": [MR("{", "{}", 9, 11)]},
            11: {"e": [MR("{", "{}", 9, 11)]},
        },
    ),
    (
        "([{]})",
        {
            0: {"s": [MR("(", "([{]})", 0, 6)]},
            1: {"s": [MR("[", "[{]", 1, 4)], "c": [MR("(", "([{]})", 0, 6)]},
            2: {
                "s": [MR("{", "{]}", 2, 5)],
                "c": [MR("(", "([{]})", 0, 6), MR("[", "[{]", 1, 4)],
            },
            4: {
                "e": [MR("[", "[{]", 1, 4)],
                "c": [MR("(", "([{]})", 0, 6), MR("{", "{]}", 2, 5)],
            },
            5: {"e": [MR("{", "{]}", 2, 5)], "c": [MR("(", "([{]})", 0, 6)]},
            6: {"e": [MR("(", "([{]})", 0, 6)]},
        },
    ),
]


@pytest.mark.parametrize(("text", "expected"), SWEEP_SPANS_RESULTS)
def test_sweep_spans(text, expected):
    assert DocResult.line_sweep_spans(gen_matches(text, MATCH_PATTERN)) == expected


## Test summarize_match_result_terms

DOC_TEXT_SMRT = "This is a test of precision and recall"
MATCH_PATTERN_SMRT = MP(r"\bprecision\b|\brecall\b")
MATCH_RESULTS_SMRT = [
    MR(MATCH_PATTERN_SMRT, "precision", 18, 27, doc_text=DOC_TEXT_SMRT),
    MR(MATCH_PATTERN_SMRT, "recall", 32, 38, doc_text=DOC_TEXT_SMRT),
]


def test_summarize_match_result_terms_base():
    r = summarize_match_result_terms(MATCH_RESULTS_SMRT)
    assert list(r.values())[0] == {"precision": 1, "recall": 1}
    assert isinstance(list(r.keys())[0], MP)


def test_summarize_match_result_terms_args():
    r = summarize_match_result_terms(MATCH_RESULTS_SMRT)
    assert list(r.values())[0] == {"precision": 1, "recall": 1}
    assert isinstance(list(r.keys())[0], MP)
    r = summarize_match_result_terms(MATCH_RESULTS_SMRT, concept_key=True)
    assert "Test" in r
    r = summarize_match_result_terms(MATCH_RESULTS_SMRT, counter_value=False)
    assert list(r.values())[0] == ["precision", "recall"]
    r = summarize_match_result_terms(MATCH_RESULTS_SMRT, counter_value_as_dict=False)
    assert list(r.values())[0] == {"precision": 1, "recall": 1}
    assert isinstance(list(r.values())[0], Counter)


def test_to_from_dict_doc():
    document_text = "This is a test"
    doc1 = Document("test", document_text)
    assert Document.from_dict(doc1.to_dict()).name == doc1.name
    doc_result1 = DocResult(doc1, {})
    dr1_test = DocResult.from_dict(doc_result1.to_dict())
    print(doc_result1)
    print(dr1_test)
    assert dr1_test.doc.name == doc_result1.doc.name
