import re
from pathlib import Path

import pytest

from leat.search import Search
from leat.search.result import DocResult
from leat.search.writer import HTMLWriter

TEST_DATA_DIRECTORY = Path(__file__).parent.parent / "data"

CONFIG_FILE = TEST_DATA_DIRECTORY / "config" / "Test-Search-Overlapping-Spans.json"
DOC_FILE = TEST_DATA_DIRECTORY / "docset1" / "simple-document-1.txt"
RESULT_1 = TEST_DATA_DIRECTORY / "ref-results" / "simple-document-1-html-writer.html"

COLOR_SCHEME = {
    "concept_colors": {
        "Test": "#088F8F",  # blue green
        "Performance Metrics": "#00FF00",  # green
        "Ethical Principles": "#0096FF",  # bright blue
        "Data Ethics": "#87CEEB",  # sky blue
        "Be Verbs": "#800000",  # maroon
        "Conjunctions": "#800000",  # maroon
        "Articles": "#800000",  # maroon
        "Clause": "#ADD8E6",  # light blue
        "First 7": "#ADD8E6",  # light blue
        "Second 5": "#FF0000",  # red
    }
}


def load_results():
    results = []
    for doc_result in Search(CONFIG_FILE, str(DOC_FILE)).search_documents(
        section_sep=5
    ):
        results.append(doc_result)
    assert len(results) == 1
    return results[0]


def test_load_results():
    results = load_results()
    assert Path(results.doc.name).stem == DOC_FILE.stem
    assert len(results.all_results()) > 1
    assert len(results.all_results()) == 38


def test_html_writer():
    results = load_results()
    w = HTMLWriter(start_pad=10, end_pad=15, scheme=COLOR_SCHEME)
    w.write_doc_result(results)
    html = w.stream.getvalue()
    assert "2022" in html
    assert "Performance Metrics" in html
    assert "Performance Metrics; First 7; First 10; Second 5" in html
    assert (
        '<span style="background-color:#aeea8f" title="Performance Metrics; First 7; First 10">Recal</span>'
        in html
    )
    assert (
        '<span style="background-color:#ea8752" title="Performance Metrics; First 7; First 10; Second 5">l</span>'
        in html
    )


def test_html_writer_exact():
    results = load_results()
    results.doc.name = results.doc.name.stem
    with open(RESULT_1, "r") as ifp:
        comparison_doc = ifp.read()
    w = HTMLWriter(start_pad=10, end_pad=15, scheme=COLOR_SCHEME)
    w.write_doc_result(results)
    html = w.stream.getvalue()
    assert comparison_doc == html
