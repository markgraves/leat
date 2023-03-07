from pathlib import Path

import pytest

from leat.store.core import DocStore
from leat.store.filesys import LocalFileSys
from leat.search.config import ConfigData
from leat.search import Search
from leat.search.result import DocResult


TEST_DATA_DIRECTORY = Path(__file__).parent.parent / "data" / "docset1"

MATCH_RESULT_TERM_RESULTS = {
    "Performance Metrics": {
        "recall": 2,
        "sensitivity": 2,
        "precision": 1,
        "specificity": 1,
    },
    "Data Ethics": {"Fairness": 1, "bias": 1, "equity": 1},
    "Ethical Principles": {"justice": 2},
    "Test": {"2022": 1},
}


def test_local_filesys():
    local_filesys = LocalFileSys()
    local_filesys.add_directory(TEST_DATA_DIRECTORY, recursive=False)
    files = local_filesys.get_files()
    print(files)
    assert len(files) >= 1


def get_doc_store():
    local_filesys = LocalFileSys()
    local_filesys.add_directory(
        TEST_DATA_DIRECTORY, include="simple-document-1.txt", recursive=False
    )
    doc_store = DocStore(local_filesys, filetypes=["text"])
    return doc_store


def get_doc():
    doc_store = get_doc_store()
    docs = [d for d in doc_store]
    assert len(docs) == 1
    return docs[0]


def test_doc_store():
    doc_store = get_doc_store()
    docs = [d for d in doc_store]
    assert len(docs) == 1
    assert get_doc().name.name == "simple-document-1.txt"


def test_doc_store_load():
    assert get_doc().text.startswith("Simple Document")


def test_config_data():
    config_data = ConfigData(predefined_configuration="BasicSearch")
    assert "BasicSearch" in config_data.short_name


def test_search():
    config_data = ConfigData(predefined_configuration="BasicSearch")
    doc_store = get_doc_store()
    searcher = Search(config_data, doc_store)
    # config has more than one match pattern
    assert len(searcher.match_patterns) > 1
    results = [r for r in searcher.search_documents(section_sep=0)]
    # only one doc result
    assert len(results) == 1
    doc_result = results.pop()
    assert doc_result.doc.name == get_doc().name
    all_matches = doc_result.all_results()
    all_matched_tokens = [m.match.group(0) for m in all_matches]
    for keyword in ["2022", "precision", "recall", "sensitivity", "specificity"]:
        assert keyword in all_matched_tokens
    concept_matches = doc_result.all_results(concept="Data Ethics")
    # more than one pattern for data ethics should have matched
    assert len(set(mr.pattern for mr in concept_matches)) > 1
    print(
        doc_result.summarize_match_result_terms(
            concept_key=True, counter_value_as_dict=True
        )
    )
    assert (
        doc_result.summarize_match_result_terms(
            concept_key=True, counter_value_as_dict=True
        )
        == MATCH_RESULT_TERM_RESULTS
    )


def test_to_from_dict():
    config_data = ConfigData(predefined_configuration="BasicSearch")
    doc_store = get_doc_store()
    searcher = Search(config_data, doc_store)
    results = [r for r in searcher.search_documents(section_sep=0)]
    doc_result = results.pop()
    assert doc_result.doc.name == get_doc().name
    dr_original = doc_result
    dr_test = DocResult.from_dict(
        dr_original.to_dict(include_text=True, compact_match_result=False)
    )
    assert dr_original.doc.name == dr_test.doc.name
    dr_original_result_pat1 = list(dr_original.pat_results.keys())[0]
    dr_test_result_pat1 = list(dr_test.pat_results.keys())[0]
    assert dr_original_result_pat1.concept == dr_test_result_pat1.concept
    assert dr_original_result_pat1.pattern == dr_test_result_pat1.pattern
    assert dr_original_result_pat1.flags == dr_test_result_pat1.flags
    assert dr_original_result_pat1.source == dr_test_result_pat1.source
    assert dr_original_result_pat1.metadata == dr_test_result_pat1.metadata
    dr_original_result_pat2 = list(dr_original.pat_results.keys())[1]
    dr_test_result_pat2 = list(dr_test.pat_results.keys())[1]
    assert dr_original_result_pat2.concept == dr_test_result_pat2.concept
    assert dr_original_result_pat2.pattern == dr_test_result_pat2.pattern
    assert dr_original_result_pat2.flags == dr_test_result_pat2.flags
    dr_original_result_val1_1 = list(dr_original.pat_results.values())[0][0]
    dr_test_result_val1_1 = list(dr_test.pat_results.values())[0][0]
    assert dr_original_result_val1_1.start == dr_test_result_val1_1.start
    assert dr_original_result_val1_1.end == dr_test_result_val1_1.end
    assert dr_original_result_val1_1.match_text == dr_test_result_val1_1.match_text
    assert (
        dr_original_result_val1_1.pattern.concept
        == dr_test_result_val1_1.pattern.concept
    )
    assert (
        dr_original_result_val1_1.pattern.pattern
        == dr_test_result_val1_1.pattern.pattern
    )
    assert (
        dr_original_result_val1_1.pattern.flags == dr_test_result_val1_1.pattern.flags
    )
    assert dr_original_result_val1_1.doc.name == dr_test_result_val1_1.doc.name


def test_to_from_dict_compact():
    config_data = ConfigData(predefined_configuration="BasicSearch")
    doc_store = get_doc_store()
    searcher = Search(config_data, doc_store)
    results = [r for r in searcher.search_documents(section_sep=0)]
    doc_result = results.pop()
    assert doc_result.doc.name == get_doc().name
    dr_original = doc_result
    dr_test = DocResult.from_dict(dr_original.to_dict())
    assert dr_original.doc.name == dr_test.doc.name
    dr_original_result_pat1 = list(dr_original.pat_results.keys())[0]
    dr_test_result_pat1 = list(dr_test.pat_results.keys())[0]
    assert dr_original_result_pat1.concept == dr_test_result_pat1.concept
    assert dr_original_result_pat1.pattern == dr_test_result_pat1.pattern
    assert dr_original_result_pat1.flags == dr_test_result_pat1.flags
    assert dr_original_result_pat1.source == dr_test_result_pat1.source
    assert dr_original_result_pat1.metadata == dr_test_result_pat1.metadata
    dr_original_result_pat2 = list(dr_original.pat_results.keys())[1]
    dr_test_result_pat2 = list(dr_test.pat_results.keys())[1]
    assert dr_original_result_pat2.concept == dr_test_result_pat2.concept
    assert dr_original_result_pat2.pattern == dr_test_result_pat2.pattern
    assert dr_original_result_pat2.flags == dr_test_result_pat2.flags
    dr_original_result_val1_1 = list(dr_original.pat_results.values())[0][0]
    dr_test_result_val1_1 = list(dr_test.pat_results.values())[0][0]
    assert dr_original_result_val1_1.start == dr_test_result_val1_1.start
    assert dr_original_result_val1_1.end == dr_test_result_val1_1.end
    assert dr_original_result_val1_1.match_text == dr_test_result_val1_1.match_text
    assert (
        dr_original_result_val1_1.pattern.concept
        == dr_test_result_val1_1.pattern.concept
    )
    assert (
        dr_original_result_val1_1.pattern.pattern
        == dr_test_result_val1_1.pattern.pattern
    )
    assert (
        dr_original_result_val1_1.pattern.flags == dr_test_result_val1_1.pattern.flags
    )
    assert dr_original_result_val1_1.doc.name == dr_test_result_val1_1.doc.name
