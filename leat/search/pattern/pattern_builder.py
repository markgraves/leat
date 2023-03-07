"""Build match patterns for search"""

from collections import defaultdict
import re

from ..config import ConfigData
from . import MatchPattern


class PatternBuilder:
    @staticmethod
    def build(configdata: ConfigData, metadata={}, super_pattern=False):
        "Build match pattern list from configdata"
        match_patterns, spattern = build_config_match_patterns(
            configdata.data,
            configdata.config_file,
            metadata,
            super_pattern=super_pattern,
        )
        if super_pattern:
            # print(spattern)
            return match_patterns, spattern
        else:
            return match_patterns


def build_config_match_patterns(
    config, source_name="", metadata={}, super_pattern=False, allow_wildcards=True
):
    "Build list of match patterns from a config dict"
    if super_pattern:
        super_trie = Trie(allow_wildcards=allow_wildcards)
    else:
        super_trie = None
    result = []
    all_patterns = []
    for sheet_name, sheet_config in config.items():
        sheet_type = sheet_config.get(
            "_sheet_type", ConfigData.get_sheetname_type(sheet_name)
        )
        source = sheet_name if not source_name else str(source_name) + "::" + sheet_name
        print("DEBUG:", "Processing", sheet_type, "sheet:", sheet_name)
        if sheet_type == "SEARCH":
            result.extend(
                build_match_patterns_search(
                    sheet_config,
                    source,
                    {"source_type": sheet_type},
                    super_trie=super_trie,
                    allow_wildcards=allow_wildcards,
                )
            )
        elif sheet_type == "PATTERN":
            pats = build_match_patterns_pattern(
                sheet_config, source, {"source_type": sheet_type}
            )
            result.extend(pats)
            if super_pattern:
                all_patterns.extend(pats)
    if super_pattern:
        if all_patterns:
            return result, r"\b" + super_trie.pattern() + r"\b|" + "|".join(
                all_patterns
            )
        else:
            return result, r"\b" + super_trie.pattern() + r"\b"
    return result, None


def build_match_patterns_search(
    config_data, source_name="", metadata={}, super_trie=None, allow_wildcards=True
):
    "Build list of match patterns from config data for a search sheet"
    result = []
    for concept, term_list in config_data.items():
        if concept.startswith("_"):
            continue
        pattern_string = create_terms_pattern(
            term_list, super_trie=super_trie, allow_wildcards=allow_wildcards
        )
        if pattern_string is None:
            continue
        # print("DEBUG:", "Building search pattern", pattern_string)
        flags = re.IGNORECASE
        match_pattern = MatchPattern(
            concept,
            pattern_string,
            re.compile(pattern_string, flags),
            flags,
            source_name,
            metadata,
        )
        result.append(match_pattern)
    return result


def build_match_patterns_pattern(config_data, source_name="", metadata={}):
    "Build list of match patterns from config data for a pattern sheet"
    result = []
    for pattern_concept, pats in config_data.items():
        if type(pattern_concept) == str and pattern_concept.startswith("_"):
            continue
        pattern_string = "|".join(pats)
        match_pattern = MatchPattern(
            pattern_concept.concept,
            pattern_string,
            re.compile(pattern_string, pattern_concept.flags),
            pattern_concept.flags,
            source_name,
            metadata,
        )
        result.append(match_pattern)
    return result


def create_terms_pattern_wo_trie(terms, allow_wildcards=True):
    "Create a regex pattern string from a list of terms"
    if terms:
        if allow_wildcards:
            return (
                r"\b"
                + r"\b|\b".join(
                    re.escape(t).replace(r"\*", r"\w*").replace(r"\?", r"\w?")
                    for t in terms
                    if t
                )
                + r"\b"
            )
        return r"\b(?:" + r"|".join(re.escape(t) for t in terms if t) + r")\b"


def create_terms_pattern(terms, allow_wildcards=True, super_trie=None):
    "Create a regex pattern string from a list of terms"
    if not terms:
        return
    trie = Trie(allow_wildcards=allow_wildcards)
    for term in terms:
        trie.add(term)
        if super_trie is not None:
            super_trie.add(term)
    # print(r"\b" + trie.pattern() + r"\b")
    return r"\b" + trie.pattern() + r"\b"


class Trie:
    """Regex::Trie in Python. Creates a Trie out of a list of words. The trie can be exported to a Regex pattern.
    The corresponding Regex should match much faster than a simple Regex union."""

    # Derived from https://stackoverflow.com/questions/42742810/

    def __init__(self, allow_wildcards=False):
        self.data = {}
        self.allow_wildcards = allow_wildcards

    def add(self, word):
        ref = self.data
        for char in word:
            ref[char] = ref.get(char, {})
            ref = ref[char]
        ref[""] = 1

    def dump(self):
        return self.data

    def quote(self, char):
        if self.allow_wildcards and char in "?*":
            return r"\w" + char
        return re.escape(char)

    def _pattern(self, pData):
        data = pData
        if "" in data and len(data.keys()) == 1:
            return None

        alt = []
        cc = []
        q = 0
        for char in sorted(data.keys()):
            if isinstance(data[char], dict):
                try:
                    recurse = self._pattern(data[char])
                    alt.append(self.quote(char) + recurse)
                except:
                    cc.append(self.quote(char))
            else:
                q = 1
        cconly = not len(alt) > 0

        if len(cc) > 0:
            if len(cc) == 1:
                alt.append(cc[0])
            else:
                alt.append("[" + "".join(cc) + "]")

        if len(alt) == 1:
            result = alt[0]
        else:
            result = "(?:" + "|".join(alt) + ")"

        if q:
            if cconly:
                result += "?"
            else:
                result = "(?:%s)?" % result
        return result

    def pattern(self):
        return self._pattern(self.dump())
