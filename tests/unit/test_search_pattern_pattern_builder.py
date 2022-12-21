from leat.search.pattern.pattern_builder import create_terms_pattern


def test_create_terms_pattern():
    assert create_terms_pattern(["a"]) == "\\ba\\b"
    assert create_terms_pattern(["a", "\b", "c"]) == "\\ba\\b|\\b\x08\\b|\\bc\\b"
    assert create_terms_pattern([]) == None
