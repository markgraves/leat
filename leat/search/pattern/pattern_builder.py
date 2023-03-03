"""Build match patterns for search"""

from collections import defaultdict
import re

from ..config import ConfigData
from . import MatchPattern


class PatternBuilder:
    @staticmethod
    def build(configdata: ConfigData, metadata={}):
        "Build match pattern list from configdata"
        match_patterns = build_config_match_patterns(
            configdata.data, configdata.config_file, metadata
        )
        return match_patterns


def build_config_match_patterns(config, source_name="", metadata={}):
    "Build list of match patterns from a config dict"
    result = []
    for sheet_name, sheet_config in config.items():
        sheet_type = sheet_config.get(
            "_sheet_type", ConfigData.get_sheetname_type(sheet_name)
        )
        source = sheet_name if not source_name else str(source_name) + "::" + sheet_name
        print("DEBUG:", "Processing", sheet_type, "sheet:", sheet_name)
        if sheet_type == "SEARCH":
            result.extend(
                build_match_patterns_search(
                    sheet_config, source, {"source_type": sheet_type}
                )
            )
        elif sheet_type == "PATTERN":
            result.extend(
                build_match_patterns_pattern(
                    sheet_config, source, {"source_type": sheet_type}
                )
            )
    return result


def build_match_patterns_search(config_data, source_name="", metadata={}):
    "Build list of match patterns from config data for a search sheet"
    result = []
    for concept, term_list in config_data.items():
        if concept.startswith("_"):
            continue
        pattern_string = create_terms_pattern(term_list)
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


def create_terms_pattern(terms, allow_wildcards=True):
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
