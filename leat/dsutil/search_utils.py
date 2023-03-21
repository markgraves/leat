"""Utilities to manage search results using pandas dataframes"""

from collections import Counter

import pandas as pd

from leat.search.result import DocResult


def counter_to_text(ctr, sep=","):
    "Summarize a counter (or similar dictionary) as a text string"
    if not isinstance(ctr, dict) or not ctr:
        return ""
    return sep.join(f"{term}({count})" for term, count in ctr.items())


def counter_to_total(ctr):
    "Total of a counter"
    if pd.isnull(ctr):
        return 0
    return sum(ctr.values())


def sum_counters(counter_list):
    cnt = Counter()
    for c in counter_list:
        if pd.notnull(c):
            cnt.update(c)
    if len(cnt):
        return cnt
    else:
        return {}


def series_counter_dict_expand(s):
    "Expand a Series of counter-like dicts to a DataFrame"
    return pd.DataFrame.from_records(s.tolist(), index=s.index).fillna(0).astype(int)


def search_dataframe(
    search,
    dataframe,
    file_colname: str = None,
    text_colname: str = None,
    docname_colname: str = None,
    doc_results_colname: str = "Doc Results",
):
    "Search text or filename column in dataframe, returning doc results series"
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


def doc_results_text(doc_results_s, text_colname: str = "text"):
    "Extract text from doc results documents"
    return doc_results_s.apply(lambda r: r.doc.text)


def concept_results_dataframe(
    doc_results_s,
    fold_case: bool = True,
    concept_key: bool = True,
    counter_value: bool = True,
    counter_value_as_dict: bool = False,
):
    "Expand doc results dict to a column of text match counts for each concept"
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
    doc_results_s, concept_counter_agg_fn=counter_to_total, fold_case: bool = True
):
    "Summarize each cell of counts"
    concept_matches_df = concept_results_dataframe(doc_results_s, fold_case)
    if concept_counter_agg_fn is not None:
        concept_matches_df = concept_matches_df.applymap(concept_counter_agg_fn)
    return concept_matches_df


def expand_doc_results_dataframe(
    doc_results_s, fold_case: bool = True, filter_columns=[]
):
    "Expand doc results to a DataFrame with all keys as columns"
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
    dataframe,
    file_colname=None,
    text_colname=None,
    doc_results_colname="Doc Results",
    concept_counter_agg_fn=counter_to_text,
):
    "Search text or filename column in dataframe, adding additional columns for each concept with summarized text matches"
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


def search_results_default_handler(obj):
    """Handler for pandas dataframe to json for search results"""
    if isinstance(obj, DocResult):
        return obj.to_dict()
