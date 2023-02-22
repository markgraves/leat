import pytest

from leat.search.display import mix_hex_color_strings


def test_mix_hex_color_strings():
    assert mix_hex_color_strings("#FF0000", "#00FF00", gamma=2) == "#b4b400"
    assert mix_hex_color_strings(["#FF0000", "#00FF00"], gamma=2) == "#b4b400"
