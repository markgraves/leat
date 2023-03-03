from leat.search.pattern.pattern_builder import create_terms_pattern


def test_create_terms_pattern():
    assert create_terms_pattern(["a"]) == "\\ba\\b"
    assert create_terms_pattern(["a", "b", "c"]) == "\\b[abc]\\b"
    assert create_terms_pattern([]) == None


def test_create_terms_pattern_trie():
    assert (
        create_terms_pattern(["a", "as", "abc", "d", "de"])
        == "\\b(?:a(?:(?:bc|s))?|de?)\\b"
    )
    assert create_terms_pattern(["andy", "and/or"]) == "\\band(?:/or|y)\\b"
    assert create_terms_pattern(["and/or", "and"]) == "\\band(?:/or)?\\b"
