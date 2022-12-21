import re

import pytest

from leat.search.result import DocResult


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


## sweep spans

PARENS_RE = r"\(.*?\)"
BRACKETS_RE = r"\[.*?\]"
BRACES_RE = r"\{.*?\}"
MATCH_PATTERN = r"(?=(" + "|".join([PARENS_RE, BRACKETS_RE, BRACES_RE]) + r"))"


class MR:
    def __init__(self, pattern, matched_text, start, end, doc_text=""):
        self.doc_text = doc_text
        self.pattern = pattern
        self.matched_text = matched_text
        self._start = start
        self._end = end

    def start(self):
        return self._start

    def end(self):
        return self._end

    def astext(self):
        return self.matched_text

    def __repr__(self):
        return f'MR("{self.pattern}", "{self.astext()}", {self.start()}, {self.end()})'

    def __eq__(self, other):
        return (
            self.start() == other.start()
            and self.end() == other.end()
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
