"""Creates functions for rendering templates against supplied parameters"""

from csv import DictReader
from io import StringIO, TextIOWrapper
from typing import Union

from jinja2 import Template

FileIO = Union[StringIO, TextIOWrapper]


def render_template_from_csv_file(
        template_fp: FileIO,
        csv_fp: FileIO,
        *,
        key: str = None
) -> dict:
    """Renders a Jinja2 template against a CSV file

    This function inputs a Jinja2 template file and a CSV file whose column
    headers correspond to the variables in the template fle (and, optionally, a
    string specifying a column header from the CSV file; otherwise, the first
    column in the CSV file is used) and outputs a dictionary keyed by the
    specified column and having as values the results of rendering the template
    against the row of the CSV file corresponding to the key value

    Args:
        template_fp: pointer to file or file-like object that is ready to read
            from and contains a Jinja2 template
        csv_fp: pointer to file or file-like object that is ready to read from
            and contains a CSV file with columns headers in its first row
        key: a column header from csv_fp, whose values should be used as key
            values in the dictionary generated

    Returns:
        A dictionary whose keys come from the column specified by the argument
        key (or from the first column in the CSV file, if no value is
        specified) and whose values are the template file rendered against the
        row in the CSV file corresponding to the key value

    """
    template_text = Template(template_fp.read())

    csv_file_reader = DictReader(csv_fp)
    if key is None:
        key = csv_file_reader.fieldnames[0]

    return_value = {}
    for row in csv_file_reader:
        return_value[row[key]] = template_text.render(row)

    return return_value
