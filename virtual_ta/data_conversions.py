"""Creates functions for converting between data formats"""

from csv import DictReader
from io import StringIO, TextIOWrapper
from typing import Union

from jinja2 import Template

FileIO = Union[StringIO, TextIOWrapper]


def mail_merge_from_dict(
        template_fp: FileIO,
        data_dict: dict,
) -> dict:
    """Mail merges a Jinja2 template against a dictionary of dictionaries

    This function inputs a Jinja2 template file and a dictionary of
    dictionaries, each having as keys variables in the template file, and
    outputs a dictionary with the same keys as the input dictionary and as
    values the results of rendering the template against the corresponding
    entry in the input dictionary

    Args:
        template_fp: pointer to file or file-like object that is ready to read
            from and contains a Jinja2 template
        data_dict: dictionary of dictionaries, each having as keys variables
            from the template

    Returns:
        A dictionary with the same keys as the input dictionary and as values
        the results of rendering the template against the corresponding entry
        in the input dictionary

    """

    template_text = Template(template_fp.read())

    return_value = {}
    for k in data_dict:
        return_value[k] = template_text.render(data_dict[k])

    return return_value


def convert_from_csv_to_dict(
        data_csv_fp: FileIO,
        *,
        key: str = None
) -> dict:
    """Convert CSV file to dictionary of dictionaries

    This function inputs a CSV file and outputs a dictionary keyed by the
    specified key column and having as values dictionaries encoding the row of
    the CSV file corresponding to the key value

    Args:
        data_csv_fp: pointer to file or file-like object that is ready to read
            from and contains a CSV file with columns headers in its first row
        key: a column header from data_csv_fp, whose values should be used as
            key values in the dictionary generated

    Returns:
        A dictionary of dictionaries encoding the row of the CSV file
        corresponding to the key value

    """

    csv_file_reader = DictReader(data_csv_fp)
    if key is None:
        key = csv_file_reader.fieldnames[0]

    return_value = {}
    for row in csv_file_reader:
        return_value[row[key]] = row

    return return_value


def mail_merge_from_csv_file(
        template_fp: FileIO,
        data_csv_fp: FileIO,
        *,
        key: str = None
) -> dict:
    """Mail merges a Jinja2 template against a CSV file

    This function inputs a Jinja2 template file and a CSV file whose column
    headers correspond to the variables in the template fle (and, optionally, a
    string specifying a column header from the CSV file; otherwise, the first
    column in the CSV file is used) and outputs a dictionary keyed by the
    specified column and having as values the results of rendering the template
    against the row of the CSV file corresponding to the key value

    Args:
        template_fp: pointer to file or file-like object that is ready to read
            from and contains a Jinja2 template
        data_csv_fp: pointer to file or file-like object that is ready to read
            from and contains a CSV file with columns headers in its first row
        key: a column header from data_csv_fp, whose values should be used as
            key values in the dictionary generated

    Returns:
        A dictionary whose keys come from the column specified by the argument
        key (or from the first column in the CSV file, if no value is
        specified) and whose values are the template file rendered against the
        row in the CSV file corresponding to the key value

    """

    data_dict = convert_from_csv_to_dict(data_csv_fp,key=key)

    return_value = mail_merge_from_dict(template_fp, data_dict)

    return return_value


def flatten_dict(
        data_items: dict,
        key_value_separator: str = '\n',
        items_separator: str = '\n',
        **kwargs
) -> str:
    """Convert dictionary to string with specified separators

    This function converts dictionary data_items to a string, with
    key_value_separator used to separate keys from values and items_separator
    used to separate items; in addition, options can be passed to the builtin
    function sorted

    Args:
        data_items: a dictionary whose keys and items will be treated as or
            converted to strings
        key_value_separator: used to separate keys from values
        items_separator: used to separate items
        **kwargs: options passed through to the builtin function sorted

    Returns:
        A string with key_value_separator used to separate keys from values and
        items_separator used to separate items

    """

    return_value = items_separator
    last_record_number = len(data_items)
    for n, k in enumerate(sorted(data_items.keys(), **kwargs)):
        return_value += str(k)
        return_value += key_value_separator
        return_value += str(data_items[k])
        if n < last_record_number - 1:
            return_value += items_separator

    return return_value
