"""
Utilities to visualize document results in html using pandas dataframes

Main entry functon is `write_dataframe_html`

Example::

  search = Search(configfile)
  df = dsutil.search_dataframe_concepts(
           search,
           original_df,
           text_colname='text',
           doc_results_colname='Doc Results'
       ).copy().drop(columns=['text'])
  df.set_index('Key', inplace=True)
  writer = HTMLWriter()
  with open('temp-results-table.html', 'w') as ofp:
      dsutil.write_dataframe_html(df, writer, ofp)

"""

import html
from io import StringIO
from typing import Optional

HTML_HEAD_CODE_START = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
"""

CSS_CODE = """<style>
.styled-table {
    border-collapse: collapse;
    margin: 25px 0;
    font-size: 0.9em;
    font-family: sans-serif;
    min-width: 400px;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
}
.styled-table thead tr {
    background-color: #0288d1;
    color: #ffffff;
    text-align: left;
}
.styled-table th,
.styled-table td {
    padding: 7px 10px;
}
.styled-table tbody tr {
    border-bottom: 1px solid #dddddd;
}

.styled-table tbody tr:nth-of-type(odd) {
    background-color: #f3f3f3;
}

.styled-table tbody tr:last-of-type {
    border-bottom: 2px solid #0288d1;
}

.visibility_button {
  border: none;
}
</style>
"""

JAVASCRIPT_CODE = """
<script type="text/javascript">
<!--
    function toggle_visibility(id) {
       var e = document.getElementById(id);
       if(e.style.visibility == 'visible')
          e.style.visibility = 'collapse';
       else
          e.style.visibility = 'visible';
       return false;
    }
//-->
</script>
"""

HTML_HEAD_CODE_END = """
</head>

<body>
"""

HTML_BODY_END = """
</body>
</html>
"""


def write_table_row(arr, style: str = "", index_in_first_column: bool = True) -> str:
    """
    Write row of html table.

    Args:
      arr: numpy.array: Array of values for the row
      style: str: CSS style for row (Default value = "")
      index_in_first_column: bool: if True, then use index in the first column to create a visibility button for text details (Default value = True)

    Returns:
      str: HTML for the row (with escaped content)
    """
    if style:
        result = f'<tr style="{style}"><td>'
    else:
        result = f"<tr><td>"
    if index_in_first_column:
        # result += f'<a href="#" onclick="toggle_visibility(\'i{arr[0]}\');">+</a></td><td>'
        result += f'<button type="button" class="visibility_button" onclick="toggle_visibility(\'i{arr[0]}\');"><u>+</u></button></td><td>'
        result += f"</td><td>".join(map(html.escape, arr[1:].astype(str)))
    else:
        result += f"</td><td>".join(map(html.escape, arr.astype(str)))
    result += f"</td></tr>"
    return result


def write_table_head(
    arr,
    rowtag: str = "tr",
    style: str = "",
    coltag: str = "th",
    insert_first_col: str = "+",
) -> str:
    """
    Write head of html table.

    Args:
      arr: numpy.array: Array of values for the row
      rowtag: str:  (Default value = "tr")
      style: str: CSS style for the row (Default value = "")
      coltag: str:  (Default value = "th")
      insert_first_col: str: String to insert for the first column, if not empty (Default value = "+")

    Returns:
      str: HTML for the head row (with escaped content)
    """
    if style:
        style = f' style="{style}"'
    result = f"<thead><{rowtag}{style}><{coltag}>"
    if insert_first_col:
        result += f"{insert_first_col}</{coltag}><{coltag}>"
    result += f"</{coltag}><{coltag}>".join(map(html.escape, arr.astype(str)))
    result += f"</{coltag}></{rowtag}></thead>\n"
    return result


def write_doc_row(arr) -> str:
    """
    Write row of document dataframe table

    Args:
      arr: numpy.array: Array of values for the row

      Note: In arr, index must be in first column; html for the text details must be in last column,

    Returns:
      str: HTML for the document row (with escaped content)
    """
    #
    # rowtag = '<tr>'
    rowtag = f'<tr id="i{arr[0]}" style="visibility:collapse">'
    # rowtag = '<tr style="visibility:collapse">'
    celltag = f'<td></td><td colspan="{len(arr)-2}" style="text-align: left">'
    return write_table_row(arr[:-1]) + f"\n{rowtag}{celltag}\n" + arr[-1] + "</td></tr>"


def write_doc_table(df, stream=None) -> Optional[str]:
    """
    Write document dataframe table as html

    Dataframe has first column index, last column html for text details, and interleaving values to display in table

    Args:
      df: pandas.DataFrame: Dataframe to write
      stream: If None, create String stream and return its value, else write to stream (Default value = None)

    Returns:
      str | None: If stream is None, return string value, else function just writes to stream
    """
    if stream is None:
        stream = StringIO()
        return_string = True
    else:
        return_string = False
    stream.write(HTML_HEAD_CODE_START)
    stream.write(CSS_CODE)
    stream.write(JAVASCRIPT_CODE)
    stream.write(HTML_HEAD_CODE_END)
    stream.write('<table class="styled-table">\n')
    stream.write(write_table_head(df.columns[1:-1], style="text-align: left"))
    stream.write("<tbody>")
    stream.write("\n".join(df.apply(write_doc_row, axis=1, raw=True).values))
    stream.write("</tbody></table>\n")
    stream.write(HTML_BODY_END)
    if return_string:
        return stream.getvalue()


def write_dataframe_html(
    dataframe, writer, stream=None, doc_results_colname="Doc Results"
) -> Optional[str]:
    """
    Write dataframe to html as interspersed data row and text results row.

    Must have a column with DocResult(s), which will be formatted to html.
    Doc results can be a list, whose html will be concatenated.
    (If no DocResults, then pandas.DataFrame.to_html() should be used.)

    Args:
      dataframe: pandas.DataFrame: Dataframe to write
      writer: search.writer.HTMLWriter: Writer to format DocResult to html
      stream: If None, create String stream and return its value, else write to stream (Default value = None)
      doc_results_colname: Name of the column in the dataframe with a DocResult (or list of DocResult) (Default value = "Doc Results")

    Returns:
       str | None: If stream is None, return string value, else function just writes to stream
    """
    if stream is None:
        stream = StringIO()
        return_string = True
    else:
        return_string = False
    dataframe["doc_result_html"] = dataframe[doc_results_colname].apply(
        lambda x: writer.get_doc_result_html(x)
        if not isinstance(x, list)
        else "\n".join(writer.get_doc_result_html(d) for d in x)
    )
    write_doc_table(dataframe.drop(columns=[doc_results_colname]).reset_index(), stream)
    if return_string:
        return stream.getvalue()
