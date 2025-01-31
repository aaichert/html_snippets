import base64
import io
from tqdm import tqdm
import uuid

table_sort_script = """
<script>
    // This script is the Search/Filter functionality.
    var TableFilter = (function(myArray) {
        var search_input;
        function _onInputSearch(e) {
            search_input = e.target;
            var tables = document.getElementsByClassName(search_input.getAttribute('data-table'));
            myArray.forEach.call(tables, function(table) {
                myArray.forEach.call(table.tBodies, function(tbody) {
                    myArray.forEach.call(tbody.rows, function(row) {
                        var text_content = row.textContent.toLowerCase();
                        var search_val = search_input.value.toLowerCase();
                        row.style.display = text_content.indexOf(search_val) > -1 ? '' : 'none';
                    });
                });
            });
        }
        return {
            init: function() {
                var inputs = document.getElementsByClassName('search-input');
                myArray.forEach.call(inputs, function(input) {
                    input.oninput = _onInputSearch;
                });
            }
        };
    })(Array.prototype);

    TableFilter.init();
</script>

<script>
    // This script is the Sorting functionality.
    const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;
    const comparer = (idx, asc) => (a, b) => ((v1, v2) =>
        v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
        )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

    // do the work...
    document.querySelectorAll("tr.sortable_columns > th").forEach(th => th.addEventListener('click', (() => {
        const table = th.closest('table')
        const tbody = table.querySelectorAll('tbody')[0];
        Array.from(tbody.querySelectorAll('tr:nth-child(n+1)'))
            .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
            .forEach(tr => tbody.appendChild(tr) );
    })));
</script>
"""

table_style = """
<style>
    .preface {background-color: white;}
    .fixed_header{
      overflow-y: scroll;
      flex-grow: 1;
    }
    .fixed_header th{
        position: sticky;
        z-index: 3;
        top: 0;
    }
    #html_snippets_table th:hover {background-color: rgb(133, 67, 16);}
    #html_snippets_table {
      font-family: Arial, Helvetica, sans-serif;
      border-collapse: collapse;
      width: 100%;
      background-color: white;
    }
    #html_snippets_table td, #html_snippets_table th {
      border: 1px solid #ddd;
      padding: 8px;
    }
    #html_snippets_table tr:nth-child(even){background-color: #f2f2f2;}
    #html_snippets_table tr:hover {background-color: #ddd;}
    #html_snippets_table th {
      padding-top: 12px;
      padding-bottom: 12px;
      text-align: left;
      background-color: #505050;
      color: white;
    }
    #html_snippets_table :target {
      color: red;
	  border-color: darkred;
      border-style: double;
    }
</style>
"""


def longest_common_prefix(strings):
    min_length = min(len(s) for s in strings)
    prefix = ""
    for i in range(min_length):
        char = strings[0][i]
        if all(s[i] == char for s in strings):
            prefix += char
        else:
            break
    return prefix


def collect_prefixes(lst):
    """A heuristic used to guess common prefixes."""
    lists = [[]]
    for item in lst:
        if len(lists[-1]) == 0 or lists[-1][0][:3] == item[:3]:
            lists[-1] += [item]
        else:
            lists += [[item]]
    
    return {longest_common_prefix(lst): lst if len(lst)>1 else [] for lst in lists}


def create_fancy_table_header(data):
    """Helper function for fancy headers spanning two rows.
    Example: html_table with "Position X" and "Position Y" and fance_header=True:
                 | Position  |                 
     | id  | foo | X   | Y   | bar | ...       |
     |-----------------------------------------|
     | ... | ... | ... | ... | ... |...        |
     
    See also: collect_prefixes
    """
    header_html = "  <thead>\n    <tr>\n"
    colgroup_html = '  <colgroup>\n'
    colspan = 0

    # Iterate over dictionary keys and values
    for key, value in data.items():
        # If the value is not an empty list
        if len(value) > 1:
            # Calculate colspan and add the first row of headers
            colspan = max(colspan, len(value))
            colgroup_html += f"      <col span='{len(value)}'>\n"
            header_html += f"       <th colspan='{len(value)}' style='border-bottom: 1px solid white;border-right: 1px solid white;'>{key.replace('_', ' ')}</th>\n"
            value_no_prefix = [l[len(key):] for l in value]
            value.clear()
            value += value_no_prefix
        else:
            # Add an empty header for keys with an empty list value
            header_html += "       <th colspan='1'></th>\n"
            colgroup_html += f"    <col span='1'>\n"
            value += [key]
    colgroup_html += '  </colgroup>\n'
    
    header_html += "    </tr>\n    <tr  class='sortable_columns'>\n"

    # Add the second row of headers
    for key, value in data.items():
        # If the value is not an empty list
        if value:
            for item in value:
                header_html += f"       <th>{item.replace('_', ' ')}</th>\n"
        else:
            # Add the key as a single column header
            header_html += f"       <th>{key.replace('_', ' ')}</th>\n"

    header_html += "    </tr>\n  </thead>\n"

    return header_html, colgroup_html


def html_table(table_data, identifier='id', simple=False, fancy_header=False, preface=None, appendix=None,
                caption=None, summary=None, highlight_rows=[], fixed_header=[], common_path="", thumbnail_size=[64, 64]):
    """
    Generates an HTML table from a list of dictionaries representing tabular data.

    Args:
        table_data (list of dict): List of dictionaries representing the table.
        identifier (str): Column used for html anchors (e.g. file.html#<id> will scroll to a row) 
        simple (bool): If True, generates a simple table without styling and scripting.
        fancy_header (bool): If True, generates two row table header by collecting common prefixes.
        
        preface (str): Additional HTML code to be inserted before the table.
        appendix (str): Additional HTML code to be inserted after the table.
        caption (str): Title of table shown above.
        summary (str): Explanation what is shown in the table.
        highlight_rows: (list of int): Rows that are highlighted
        fixed_header: these header elements will be forced to be in that order and at the left of the table.
        common_path (str): Common path for thumbnail images, if applicable.
        thumbnail_size (list): List containing width and height of thumbnail images.

    Returns:
        tuple: A tuple containing HTML code for the table head, body, and tail.
    """

    # Identifier to differentiate between multiple tables for sorting and searching
    table_uid = str(uuid.uuid4())[:6]
    
    table_headers = [] + fixed_header   #  <-- BUG?!
    for row in table_data:
        for key in row.keys():
            if not key in table_headers:
                table_headers += [key]
    
    colgroup_html = ''

    if not simple:
        # This is the minimal html code to create a searchable and sortable list
        head = table_style.replace('html_snippets_table', f'table_{table_uid}')
        tail = table_sort_script.replace('html_snippets_table', f'table_{table_uid}')

        body = preface if preface else ""

        body += f'<input type="search" placeholder="Search..." class="form-control search-input" data-table="table_{table_uid}" style="margin: 10px; padding 4px;"/><br>\n'
    else:
        # Simple case: we just display a table, not using any javascript
        head = tail = body = ""

    if summary is not None:
        body += f'<span>{summary}</span>\n'

    body += f"<table  id=\"table_{table_uid}\" class=\"fixed_header sortable colon_data\">\n"  # fixme: remove sortable? I have sortable_columns class now.

    if caption is not None:
        body += f'  <caption>{caption}</caption>\n'
        
    if fancy_header:
        # Group columns with common prefix and show a second table header.
        header_dict = collect_prefixes(table_headers)
        header_html, colgroup_html =  create_fancy_table_header(header_dict)
        body += colgroup_html
        body += header_html
    else:
        body += "  <thead>\n"
        body += "    <tr class='sortable_columns'>\n"
    
        for header in table_headers:
            body += f"      <th>{header}</th>\n"
    
        body += "    </tr>\n"
        body += "  </thead>\n"

    # Write the actual table rows
    body += "  <tbody>\n"
    if not simple and len(table_data) > 100:
        table_data = tqdm(table_data)
    for idx, row_data in enumerate(table_data):
        if identifier in row_data:
            id = row_data[identifier]
            anchor = f' id="{id}"'
        else:
            anchor = ""
        if idx in highlight_rows:
            highlight_style = " style='border: 1px solid orange;'"
        else:
            highlight_style = ''
        body += f"    <tr{anchor}{highlight_style}>\n"
        for entry in table_headers:
            if entry in row_data:
                body += f"      <td>{row_data[entry]}</td>\n"
            else:
                body += f"      <td> </td>\n"
        body += "    </tr>\n"
    body += "  </tbody>\n"

    body += "</table>\n"
    body += "\n"
    if appendix is not None:
        body += appendix
    body += "\n"

    return head, body, tail


# And some utility:

def mix_colors(rel, rgb0=(255, 0, 0), rgb1=(0, 255, 0)):
    """Maps a normalized value [0,1] to a mix of two rgb colors.

    Args:
        rel (float): Normalized value between 0 and 1.
        rgb0: RGB color tuple of an RGB color in [0,255] range
        rgb1: RGB color tuple of an RGB color in [0,255] range

    Returns:
        tuple: RGB color tuple representing the color corresponding to the normalized value.  
    """
    r = round(rgb0[0]*(1.0 - rel) + rgb1[0]*rel)
    g = round(rgb0[1]*(1.0 - rel) + rgb1[1]*rel)
    b = round(rgb0[2]*(1.0 - rel) + rgb1[2]*rel)
    return r, g, b


def red_to_green(rel):
    """See also: mix_colors(...)"""
    return mix_colors(rel)


def green_to_red(rel):
    """See also: mix_colors(...)"""
    return mix_colors(rel, rgb0=(0, 255, 0), rgb1=(255, 0, 0))


def color_code(table_data, key, vmin, vmax, color_lut=green_to_red):
    """Color-codes the values in a specified column of each row in the table_data based on a given color lookup table.
    See also: mix_colors(...)
    
    Args:
        table_data (list of dict): List of dictionaries representing the table.
        key (str): The key (column) whose values will be color-coded.
        vmin (float): Minimum value for normalization.
        vmax (float): Maximum value for normalization.
        color_lut (function): A color lookup table function that maps normalized values to RGB color tuples.
    
    Returns:
        None (modifies the input table_data in-place).
    """
    for row in table_data:
        try:
            value = float(row[key])
            if vmin == vmax:
                rel = 0 if value<=vmin else 1
            else:
                rel = (value-vmin) / (vmax-vmin)
            if rel < 0:
                rel = 0
            if rel > 1:
                rel =1
            r, g, b = color_lut(rel)
            row[key] = f'<span style="color:rgb({r}, {g}, {b});">{row[key]}</span>'
        except:
            if key in row and not (isinstance(row[key],str) and row[key].startswith('<span style=')):
                row[key] = f'<b>{row[key]}</b>'


def transform_column(table_data, key, transformation_function):
    """
    Applies a transformation function to a specified column in each row of the table_data.

    Args:
        table_data (list of dict): List of dictionaries representing the table.
        key (str): The key (column) to be transformed in each row.
        transformation_function (function): A function to be applied to the values of the specified key.

    Returns:
        None (modifies the input table_data in-place).
    """
    for row in table_data:
        if key in row:
            row[key] = transformation_function(row[key])


def rename_column(table_data, key, new_key):
    """
    Changes the name of a column

    Args:
        table_data (list of dict): List of dictionaries representing the table.
        key (str): The key (column) to be renamed.
        new_kew (str): The new name for the key.

    Returns:
        None (modifies the input table_data in-place).
    """
    for row in table_data:
        new_row = dict()
        for k, v in row.items():
            if k == key:
                k = new_key
            new_row[k] = v
        row.clear()
        row.update(new_row)
        

def sort_rows(table_data, key, reverse=False):
    """
    Sorts the rows in the table_data based on the specified key.
    
    Args:
        table_data (list of dict): List of dictionaries representing the table.
        key (str): The key by which the rows should be sorted.
        reverse (bool): If True, sorts in descending order; otherwise, ascending order.

    Returns:
        None (modifies the input table_data in-place).
    """
    table_data.sort(key=lambda x: x[key], reverse=reverse)


def remove_columns(table_data, keys):
    """
    Removes specified columns from each row in the table_data.

    Args:
        table_data (list of dict): List of dictionaries representing the table.
        keys (list): List of keys (columns) to be removed from each row.

    Returns:
        None (modifies the input table_data in-place).
    """
    for row in table_data:
        for key in keys:
            try:
                del row[key]
            except:
                pass
