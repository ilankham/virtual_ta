"""Creates functions for converting between data formats"""

from calendar import day_name
from csv import DictReader
from datetime import date
from io import BytesIO, FileIO, StringIO, TextIOWrapper
from typing import Union

from jinja2 import Template
from openpyxl import load_workbook

FileIO = Union[BytesIO, FileIO, StringIO, TextIOWrapper]


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


def convert_csv_to_dict(
        data_csv_fp: FileIO,
        *,
        key: str = None,
) -> dict:
    """Convert CSV file to dictionary of dictionaries

    This function inputs a CSV file and an optional key column (defaulting to
    the left-most column, if not specified) and outputs a dictionary keyed by
    the specified key column and having as values dictionaries encoding the row
    from the CSV file corresponding to the key value

    Args:
        data_csv_fp: pointer to file or file-like object that is ready to read
            from and contains a CSV file with columns headers in its first row
        key: a column header from data_csv_fp, whose values should be used as
            key values in the dictionary generated

    Returns:
        A dictionary keyed by the specified key column and having as values
        dictionaries encoding the row from the CSV file corresponding to the
        key value

    """

    csv_file_reader = DictReader(data_csv_fp)
    if key is None:
        key = csv_file_reader.fieldnames[0]

    return_value = {}
    for row in csv_file_reader:
        return_value[row[key]] = row

    return return_value


def convert_xlsx_to_dict(
        data_xlsx_fp: FileIO,
        *,
        key: str = None,
        worksheet: str = None,
) -> dict:
    """Convert XLSX file to dictionary of dictionaries

    This function inputs an XLSX file, an optional key column (defaulting to the
    left-most column, if not specified), and an optional worksheet name column
    (defaulting to the first worksheet, if not specified), and outputs a
    dictionary keyed by the specified key column and having as values
    dictionaries encoding the row from the specified worksheet of the XLSX file
    corresponding to the key value

    Args:
        data_xlsx_fp: pointer to file or file-like object that is ready to read
            from and contains an XLSX file with columns headers in first rows
        key: a column header from data_xlsx_fp, whose values should be used as
            key values in the dictionary generated
        worksheet: a worksheet name from data_xlsx_fp

    Returns:
        A dictionary keyed by the specified key column and having as values
        dictionaries encoding the row from the specified worksheet of the XLSX
        file corresponding to the key value

    """

    xlsx_file_reader = load_workbook(data_xlsx_fp, read_only=True)
    if worksheet is None:
        worksheet = xlsx_file_reader[0]
    if key is None:
        key = worksheet.cell(row=1, column=1)

    xlsx_worksheet_reader = xlsx_file_reader[worksheet]
    xlsx_worksheet_columns = xlsx_worksheet_reader.rows
    xlsx_worksheet_headers = [
        cell.value
        for cell in next(xlsx_worksheet_columns)
    ]
    key_column_index = xlsx_worksheet_headers.index(key)

    return_value = {}
    for i, row in enumerate(xlsx_worksheet_columns):
        new_row_to_add = {}
        for j, cell in enumerate(row):
            new_row_to_add[xlsx_worksheet_headers[j]] = row[j].value
        return_value[row[key_column_index].value] = new_row_to_add

    return return_value


def convert_xlsx_to_yaml_calendar(
        data_xlsx_fp: FileIO,
        start_date: date,
        *,
        item_delimiter: str = "|",
        week_number_column: str = None,
        worksheet: str = None,
) -> str:
    # start day will be adjusted to Monday of the week that start_date
    # appears in, where weeks are defined as running from Monday to Sunday
    #
    # Week numbers in the week_number_column column of data_xlsx_fp should be
    # integers, with 1 the week that start_date appears in
    #
    # day names use current locale, as identified by calendar module, in ISO
    # 8601 order, Monday through Sunday
    
    data_dict = convert_xlsx_to_dict(
        data_xlsx_fp,
        key=week_number_column,
        worksheet=worksheet
    )

    # check whether start_date needs to be rounded to start of next week

    # for each data, map day of week to number using
    # [day.lower() for day in day_name]


def mail_merge_from_csv_file(
        template_fp: FileIO,
        data_csv_fp: FileIO,
        *,
        key: str = None,
) -> dict:
    """Mail merges a Jinja2 template against a CSV file

    This function inputs a Jinja2 template file a CSV file, and an optional key
    column (defaulting to the left-most column, if not specified) and outputs a
    dictionary keyed by the specified column and having as values the results
    of rendering the template against the row from the CSV file corresponding
    to the key value

    Args:
        template_fp: pointer to file or file-like object that is ready to read
            from and contains a Jinja2 template
        data_csv_fp: pointer to file or file-like object that is ready to read
            from and contains a CSV file with columns headers in its first row
        key: a column header from data_csv_fp, whose values should be used as
            key values in the dictionary generated

    Returns:
        A dictionary keyed by the specified column and having as values the
        results of rendering the template against the row from the CSV file
        corresponding to the key value

    """

    data_dict = convert_csv_to_dict(data_csv_fp, key=key)

    return_value = mail_merge_from_dict(template_fp, data_dict)

    return return_value


def mail_merge_from_xlsx_file(
        template_fp: FileIO,
        data_xlsx_fp: FileIO,
        *,
        key: str = None,
        worksheet: str = None,
) -> dict:
    """Mail merges a Jinja2 template against an XLSX file

    This function inputs a Jinja2 template file an XLSX file, an optional key
    column (defaulting to the left-most column, if not specified), and an
    optional worksheet name column (defaulting to the first worksheet, if not
    specified) and outputs a dictionary keyed by the specified column and
    having as values the results of rendering the template against the row from
    the specified worksheet of the XLSX file corresponding to the key value

    Args:
        template_fp: pointer to file or file-like object that is ready to read
            from and contains a Jinja2 template
        data_xlsx_fp: pointer to file or file-like object that is ready to read
            from and contains an XLSX file with columns headers in its first row
        key: a column header from data_xlsx_fp, whose values should be used as
            key values in the dictionary generated
        worksheet: a worksheet name from data_xlsx_fp

    Returns:
        A dictionary keyed by the specified column and having as values the
        results of rendering the template against the row from the specified
        worksheet of the XLSX file corresponding to the key value

    """

    data_dict = convert_xlsx_to_dict(data_xlsx_fp, key=key, worksheet=worksheet)

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
