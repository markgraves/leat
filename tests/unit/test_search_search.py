import pytest

from leat.search import Search

DOC_TEXT_1 = "This is a test of precision and recall"


def test_search():
    search = Search(predefined_configuration="BasicSearch")
    r = search.search_document_text("This is a test of precision and recall")
    assert r.doc.text == DOC_TEXT_1
    assert r.doc.name == "No Name"
    print(r.pat_results)
    assert list(r.pat_results.keys())[0].concept == "Performance Metrics"
    mr1 = list(r.pat_results.values())[0][0]
    mr2 = list(r.pat_results.values())[0][1]
    assert mr1.start() == 18
    assert mr1.end() == 27
    assert mr1.match_text == "precision"
    assert mr2.start() == 32
    assert mr2.end() == 38
    assert mr2.match_text == "recall"
