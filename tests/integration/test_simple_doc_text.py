from pathlib import Path

import pytest

from leat.store.core import DocStore
from leat.store.filesys import LocalFileSys
from leat.search.config import ConfigData
from leat.search import Search


TEST_DATA_DIRECTORY = Path(__file__).parent.parent / "data" / "docset1"


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
