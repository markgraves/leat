"""Build match patterns for search"""

from collections import defaultdict
import re
from typing import Iterable, List, Optional

from ..config import ConfigData
from . import MatchPattern


class PatternBuilder:
    """Builds match patterns from config data"""

    @staticmethod
    def build(
        configdata: ConfigData, metadata: dict = {}, super_pattern: bool = False
    ) -> List[MatchPattern]:
        """
        Build list of match pattern objects from configdata

        Args:
          configdata: ConfigData: Configuration data with the concept terms and patterns to use
          metadata: dict: Auxillary data to include in match pattern objects (Default value = {})
          super_pattern: bool: Whether to also build a pattern that matches any of the pattern text. Useful for efficient filtering of documents (Default value = False)

        Returns:
          List[MatchPattern]: List of match patterns
        """
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
    config: ConfigData,
    source_name: str = "",
    metadata: dict = {},
    super_pattern: bool = False,
    allow_wildcards: bool = True,
):
    """
    Build list of match patterns from a config dict

    Args:
      config: ConfigData: Configuration data with the concept terms and patterns
      source_name: str: Source (filename) of config data (Default value = "")
      metadata: dict:  Auxillary data to include in match pattern objects (Default value = {})
      super_pattern: bool:  Whether to also build a pattern that matches any of the pattern text. (Default value = False)
      allow_wildcards: bool: Whether to allow wildcards in the terms (Default value = True)

    Returns:
      List[MatchPattern]: List of match patterns
      Optional[str]: super pattern (if super_pattern arg is True)

    Note: Wildcards in terms are glob style (i.e., "*" or "?"), and are converted to regex style
          Matches any "word" char, i.e., alphanumeric or underscore

    """
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
        # print("DEBUG:", "Processing", sheet_type, "sheet:", sheet_name)
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
    config_data: dict,
    source_name: str = "",
    metadata: dict = {},
    super_trie: Optional["Trie"] = None,
    allow_wildcards: bool = True,
) -> List[MatchPattern]:
    """
    Build list of match patterns from config data for a search sheet

    Args:
      config_data: dict: Configuration data for a sheet in ConfigData, which has concept-terms mapping
      source_name: str: Source (filename) of config data (Default value = "")
      metadata: dict:  Auxillary data to include in match pattern objects (Default value = {})
      super_trie: Optional[Trie] Trie in which to build super pattern of all matchin terms. If None, do not build. (Default value = None)
      allow_wildcards: Whether to allow wildcards in the term patterns and trie. (Default value = True)

    Returns:
      List[MatchPattern]: List of match patterns matching the terms in the config_data

    Side Effect:
      Modifies the super_trie, if it is passed
    """
    result = []
    for concept, term_list in config_data.items():
        if concept.startswith("_"):
            continue
        uppercase_terms = []
        lowercase_terms = []
        for term in term_list:
            if term == term.upper():
                uppercase_terms.append(term)
            else:
                lowercase_terms.append(term)
        for flags in (0, re.IGNORECASE):  # re.NOFLAG # noflag in python 3.11
            current_terms = lowercase_terms if flags else uppercase_terms
            pattern_string = create_terms_pattern(
                current_terms, super_trie=super_trie, allow_wildcards=allow_wildcards
            )
            if pattern_string is None:
                continue
            # print("DEBUG:", "Building search pattern", pattern_string)
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


def build_match_patterns_pattern(
    config_data: dict, source_name: str = "", metadata: dict = {}
):
    """
    Build list of match patterns from config data for a pattern sheet

    Args:
      config_data: dict: Configuration data for a sheet in ConfigData, which has concept-patterns mapping
      source_name: Source (filename) of config data (Default value = "")
      metadata: Auxillary data to include in match pattern objects (Default value = {})

    Returns:
      List[MatchPattern]: List of match patterns matching the terms in the config_data
    """
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


def create_terms_pattern_wo_trie(
    terms: Iterable[str], allow_wildcards: bool = True
) -> Optional[str]:
    """
    Create a regex pattern string from a list of terms

    Args:
      terms: Iterable[str]: Terms to combine into a pattern (as escaped words with word boundaries)
      allow_wildcards: Whether patterns are supported in the pattern (Default value = True)

    Returns:
      str | None: Pattern that matches any of the terms (Or None if no terms are passed)

    Note: Wildcards in terms are glob style (i.e., "*" or "?"), and are converted to regex style
          Matches any "word" char, i.e., alphanumeric or underscore
    """
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


def create_terms_pattern(
    terms: Iterable[str],
    allow_wildcards: bool = True,
    super_trie: Optional["Trie"] = None,
) -> str:
    """
    Create a regex pattern string from a list of terms

    Args:
      terms: Iterable[str]: Terms to combine into a pattern (as escaped words with word boundaries)
      allow_wildcards: Whether patterns are supported in the pattern (Default value = True)
      super_trie: Optional[Trie] Trie in which to build super pattern of all matchin terms. If None, do not build. (Default value = None)

    Returns:
      str: Pattern that matches any of the terms

    Note: Wildcards in terms are glob style (i.e., "*" or "?"), and are converted to regex style
          Matches any "word" char, i.e., alphanumeric or underscore

    """
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
    """
    Creates a Trie out of a list of words. The trie can be exported to a Regex pattern.
    The corresponding Regex should match much faster than a simple Regex union.

    Attributes:
      allow_wildcards: bool: Whether to allow wildcard (Default value = False)
      data: dict: The trie
    """

    # Derived from https://stackoverflow.com/questions/42742810/

    def __init__(self, allow_wildcards: bool = False):
        """
        Create a trie

        Args:
          allow_wildcards: Whether to allow wildcard (Default value = False)
        """
        self.data = {}
        self.allow_wildcards = allow_wildcards

    def add(self, word: str):
        """
        Add a word to the trie

        Args:
          word: A word to add
        """
        ref = self.data
        for char in word:
            ref[char] = ref.get(char, {})
            ref = ref[char]
        ref[""] = 1

    def dump(self) -> dict:
        """Returns the trie as a dict"""
        return self.data

    def quote(self, char: str) -> str:
        """
        Quotes/escapes a char for regex (and expands wildcards)

        Args:
          char: str: Char to quote (string of length 1)

        Returns:
          Quoted char
        """
        if self.allow_wildcards and char in "?*":
            return r"\w" + char
        return re.escape(char)

    def _pattern(self, pData):
        """
        Converts trie dictionary to a regex pattern string

        Args:
          pData: dict: Trie dictionary

        Returns:
          str: Regex pattern string
        """
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

    def pattern(self) -> str:
        """Converts trie dictionary to a regex pattern string

        Returns:
          str: Regex pattern string
        """
        return self._pattern(self.dump())
