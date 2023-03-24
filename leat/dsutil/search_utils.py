"""Utilities to manage search results using pandas dataframes"""

from collections import Counter
import re

from typing import Optional, Union, List, Iterable, Callable
import pandas as pd

from leat.search.result import DocResult


def counter_to_text(ctr: Counter, sep=",") -> str:
    """
    Summarize a counter (or similar dictionary) as a text string

    Args:
      ctr: Counter: Counter of terms
      sep: Separator for joining text (Default value = ",")

    Returns:
      str: Text string of term1(n1), term2(n2), ...
    """
    if not isinstance(ctr, dict) or not ctr:
        return ""
    return sep.join(f"{term}({count})" for term, count in ctr.items())


def counter_to_total(ctr: Counter) -> int:
    """
    Total of a counter

    Args:
      ctr: Counter:

    Returns:
      int: Sum of all values in the counter
    """
    if pd.isnull(ctr):
        return 0
    return sum(ctr.values())


def sum_counters(counter_list: Iterable[Counter]) -> Union[Counter, dict]:
    """
    Sum a list of counters into one counter, or empty dict if no items

    Args:
      counter_list: Iterable[Counter]: List of counters to sum

    Returns:
      Counter | dict: Counter summing all counters, or empty dict
    """
    cnt = Counter()
    for c in counter_list:
        if pd.notnull(c):
            cnt.update(c)
    if len(cnt):
        return cnt
    else:
        return {}


def series_counter_dict_expand(s: pd.Series) -> pd.DataFrame:
    """
    Expand a Series of counter-like dicts to a DataFrame

    Args:
      s: pd.Series: Series of counters (or counter-like dicts)

    Returns:
      pd.DataFrame: Dataframe with each term as a column and counter value as a row
    """
    return pd.DataFrame.from_records(s.tolist(), index=s.index).fillna(0).astype(int)


def search_dataframe(
    search,
    dataframe: pd.DataFrame,
    file_colname: str = None,
    text_colname: str = None,
    docname_colname: str = None,
    doc_results_colname: str = "Doc Results",
) -> pd.Series:
    """
    Search text or filename column in dataframe, returning doc results series

    Args:
      search: Search: Search object to use
      dataframe: pd.DataFrame: Dataframe with a text or filename column for searching
      file_colname: str: Column name for file that has text (Default value = None)
      text_colname: str: Column name for text to search (Default value = None)
      docname_colname: str: Column name for document name to be used to create Document (Default value = None)
      doc_results_colname: str: Column/series name for creating Doc Results (Default value = "Doc Results")

    Returns:
      Series of Doc Results
    """
    if text_colname is not None and text_colname in dataframe.columns:
        if docname_colname is None:
            doc_results_s = (
                dataframe[text_colname]
                .reset_index()
                .apply(
                    lambda a: search.search_document_text(a[1], a[0]), axis=1, raw=True
                )
            )
        else:
            doc_results_s = dataframe[[text_colname, docname_colname]].apply(
                lambda a: search.search_document_text(a[0], a[1]), axis=1, raw=True
            )
        doc_results_s.index = dataframe.index
        doc_results_s.name = doc_results_colname
    elif file_colname is not None and file_colname in dataframe.columns:
        doc_results_s = dataframe[file_colname].apply(search.read_search_document)
    else:
        print("WARNING:", "Nothing to do")
    return doc_results_s


def doc_results_text(doc_results_s: pd.Series, text_colname: str = "text") -> pd.Series:
    """
    Extract text from doc results documents

    Args:
      doc_results_s: pd.Series: Series of Doc Results
      text_colname: str: Column/series name for creating text column/series (Default value = "text")

    Returns:
      Series of Doc Results
    """
    text_s = doc_results_s.apply(lambda r: r.doc.text)
    text_s.name = text_colname
    return


def concept_results_dataframe(
    doc_results_s: pd.Series,
    fold_case: bool = True,
    concept_key: bool = True,
    counter_value: bool = True,
    counter_value_as_dict: bool = False,
) -> pd.DataFrame:
    """
    Expand doc results dict to a column of text match counts for each concept

    Args:
      doc_results_s: pd.Series: Series of Doc Results
      fold_case: bool: Fold case of terms (Default value = True)
      concept_key: bool: Use concept as key, intead of Match Pattern (Default value = True)
      counter_value: bool: Use Counter to track terms, instead of a list (Default value = True)
      counter_value_as_dict: bool: Use dict(s) in the returned result, instead of Counter (Default value = False)

    Returns:
      pd.DataFrame: Dataframe with each concept occurring in doc_results_s as a column and counters as values
    """
    temp_concept_matches = doc_results_s.apply(
        lambda x: x.summarize_match_result_terms(
            concept_key=concept_key,
            counter_value=counter_value,
            counter_value_as_dict=counter_value_as_dict,
            fold_case=fold_case,
        )
    )
    concept_matches_df = pd.DataFrame.from_records(
        temp_concept_matches.tolist(), index=temp_concept_matches.index
    ).applymap(lambda x: x if pd.notnull(x) else {})
    return concept_matches_df


def summarize_doc_results_dataframe(
    doc_results_s: pd.Series,
    concept_counter_agg_fn: Callable = counter_to_total,
    fold_case: bool = True,
) -> pd.DataFrame:
    """
    Summarize each cell of counts

    Args:
      doc_results_s: pd.Series: Series of Doc Results
      concept_counter_agg_fn: Callable: Function to aggregate across counters (Default value = counter_to_total)
      fold_case: bool: Fold case of terms (Default value = True)

    Returns:
       pd.DataFrame: Dataframe with each concept occurring in doc_results_s as a column and summarized counters as values
    """
    concept_matches_df = concept_results_dataframe(doc_results_s, fold_case)
    if concept_counter_agg_fn is not None:
        concept_matches_df = concept_matches_df.applymap(concept_counter_agg_fn)
    return concept_matches_df


def expand_doc_results_dataframe(
    doc_results_s: pd.Series, fold_case: bool = True, filter_columns=[]
) -> pd.DataFrame:
    """
    Expand doc results to a DataFrame with all keys as columns

    Note: This does not handle to case where a key occurs in more than one concept

    Args:
      doc_results_s: pd.Series: Series of Doc Results
      fold_case: bool: Fold case of terms (Default value = True)
      filter_columns: Concepts to include, filtering out all others (Default value = [])

    Returns:
      Dataframe with every key of each filter-allowed concept occurring in doc_results_s as a column
    """
    concept_matches_df = concept_results_dataframe(doc_results_s, fold_case)
    if filter_columns:
        all_concepts = set(concept_matches_df.columns).intersection(filter_columns)
    else:
        all_concepts = concept_matches_df.columns
    return pd.concat(
        [series_counter_dict_expand(concept_matches_df[col]) for col in all_concepts],
        keys=all_concepts,
        axis=1,
    )


def search_dataframe_concepts(
    search,
    dataframe: pd.DataFrame,
    file_colname=None,
    text_colname=None,
    doc_results_colname="Doc Results",
    concept_counter_agg_fn=counter_to_text,
) -> pd.DataFrame:
    """
    Search text or filename column in dataframe, adding additional columns for each concept with summarized text matches

    Args:
      search: Search: Search object to use
      dataframe: pd.DataFrame: Dataframe with a text or filename column for searching
      file_colname: Column name for file that has text (Default value = None)
      text_colname: Column name for text to search (Default value = None)
      doc_results_colname: Column name for creating Doc Results (Default value = "Doc Results")
      concept_counter_agg_fn: Function to use for aggregating counters (Default value = counter_to_text)

    Returns:
      Dataframe with each concept occurring in doc_results_s as a column and summarized counters as values
    """
    doc_results_s = search_dataframe(
        search, dataframe, file_colname, text_colname, doc_results_colname
    )
    concept_matches_df = summarize_doc_results_dataframe(
        doc_results_s, concept_counter_agg_fn
    )
    temp_df = concept_matches_df.join(dataframe, how="right")
    if text_colname is not None and text_colname not in dataframe.columns:
        temp_df[text_colname] = doc_results_text(doc_results_s, text_colname)
    temp_df[doc_results_colname] = doc_results_s
    return temp_df


def search_results_default_handler(obj) -> Optional[dict]:
    """
    Handler for pandas dataframe to json for search results

    Args:
      obj: If a DocResult, return it as a dict

    Returns:
      dict | None: Dictionary form of DocResult, or None
    """
    if isinstance(obj, DocResult):
        return obj.to_dict()


def strip_truncated_text(text: str, sep: str = r"\s"):
    """
    Strip leading and trailing characters from a string, leaving only characters after first sep and before final sep

    This is useful to ensuring only whole words/tokens are contained in an extracted text substring

    Args:
      text: str: Text to strip
      sep: str: Separation character (Default value = r"\s")

    Returns:
      str: Stripped text
    """
    first = re.search(sep, text)
    last = re.search("(?s:.*)(" + sep + ")", text)
    if first is not None:
        text = text[first.start() : last.start(1)]
    return text.strip()
