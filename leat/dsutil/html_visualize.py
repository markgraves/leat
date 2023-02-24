"""Utilities to visualize document results in html using pandas dataframes"""

import html
from io import StringIO

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


def write_table_row(arr, style="", index_in_first_column=True):
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


def write_table_head(arr, rowtag="tr", style="", coltag="th", insert_first_col="+"):
    if style:
        style = f' style="{style}"'
    result = f"<thead><{rowtag}{style}><{coltag}>"
    if insert_first_col:
        result += f"{insert_first_col}</{coltag}><{coltag}>"
    result += f"</{coltag}><{coltag}>".join(map(html.escape, arr.astype(str)))
    result += f"</{coltag}></{rowtag}></thead>\n"
    return result


def write_doc_row(arr):
    # html must be in last column, index in first column
    # rowtag = '<tr>'
    rowtag = f'<tr id="i{arr[0]}" style="visibility:collapse">'
    # rowtag = '<tr style="visibility:collapse">'
    celltag = f'<td></td><td colspan="{len(arr)-2}" style="text-align: left">'
    return write_table_row(arr[:-1]) + f"\n{rowtag}{celltag}\n" + arr[-1] + "</td></tr>"


def write_doc_table(df, stream=None):
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
):
    if stream is None:
        stream = StringIO()
        return_string = True
    else:
        return_string = False
    dataframe["doc_result_html"] = dataframe[doc_results_colname].apply(
        writer.get_doc_result_html
    )
    write_doc_table(dataframe.drop(columns=[doc_results_colname]).reset_index(), stream)
    if return_string:
        return stream.getvalue()
