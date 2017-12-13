"""Creates functions for converting between data formats"""

from calendar import day_name
from csv import DictReader
from datetime import date, timedelta
from io import BytesIO, FileIO, StringIO, TextIOWrapper
from typing import BinaryIO, TextIO, Union

from openpyxl import load_workbook
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap


FileIO = Union[BinaryIO, BytesIO, FileIO, StringIO, TextIO, TextIOWrapper]


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

    This function inputs an XLSX file, an optional key column (defaulting to
    the left-most column, if not specified), and an optional worksheet name
    column (defaulting to the first worksheet, if not specified), and outputs a
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

    xlsx_file_reader = load_workbook(
        data_xlsx_fp,
        read_only=True,
        data_only=True
    )
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
    """Convert XLSX file to YAML file representing calendar data by week number

    This function inputs an XLSX file, a start date, an optional item delimiter
    for decomposing cell values into lists (defaulting to a vertical pipe), an
    optional key column for week numbers (defaulting to the left-most column,
    if not specified), and an optional worksheet name column (defaulting to the
    first worksheet, if not specified), and outputs a string containing a YAML
    representation keyed by the specified key column and having as values
    dictionaries encoding the row from the specified worksheet of the XLSX file
    corresponding
    to the key value

    Args:
        data_xlsx_fp: pointer to file or file-like object that is ready to read
            from and contains an XLSX file with columns headers in first rows;
            any column names in data_xlsx_fp corresponding to day names in the
            current locale, as identified by the calendar module, are treated
            as providing activities for the corresponding calendar date and
            will be ordered according to ISO 8601 in output; all other columns
            are treated as providing information about the week itself
        start_date: specifies the start date for the calendar, which is
            adjusted to the Monday of the week that the start_date appears in,
            where weeks are defined as running from Monday to Sunday
        item_delimiter: a string whose values will be used to split item values
            into lists
        week_number_column: a column header from data_xlsx_fp, whose values
            should be used as key values in the YAML string generated; the
            values of the column in data_xlsx_fp should be integers, with the
            integer one (1) representing the week that start_date appears in
        worksheet: a worksheet name from data_xlsx_fp

    Returns:
         A string containing a YAML representation keyed by the specified key
         column and having as values dictionaries encoding the row from the
         specified worksheet of the XLSX file corresponding to the key value

    """

    data_dict = convert_xlsx_to_dict(
        data_xlsx_fp,
        key=week_number_column,
        worksheet=worksheet
    )

    start_date_adjusted = start_date - timedelta(days=start_date.weekday())

    weekdays_lookup_dict = {day.lower(): n for n, day in enumerate(day_name)}

    calendar_dict = CommentedMap()
    for week_number, week_data in data_dict.items():
        week_number = int(week_number)
        calendar_dict[week_number] = CommentedMap()
        for weekday in week_data:
            if weekday == week_number_column or week_data[weekday] is None:
                continue
            if weekday.lower() in weekdays_lookup_dict:
                weekday_date = (
                        start_date_adjusted
                        +
                        timedelta(
                            days=7 * (int(week_number) - 1) +
                            int(weekdays_lookup_dict[weekday.lower()])
                        )
                ).strftime('%d%b%Y').upper()
                calendar_dict[week_number][weekday] = CommentedMap()
                calendar_dict[week_number][weekday]['Date'] = weekday_date
                calendar_dict[week_number][weekday]['Activities'] = (
                    week_data[weekday].split(item_delimiter)
                )

            else:
                calendar_dict[week_number][weekday] = (
                    week_data[weekday].split(item_delimiter)
                )

    yaml = YAML()
    calendar_yaml = StringIO()
    yaml.dump(data=calendar_dict, stream=calendar_yaml)
    calendar_yaml.seek(0)

    return calendar_yaml.read()


def flatten_dict(
        data_items: dict,
        key_value_separator: str = '\n',
        items_separator: str = '\n',
        *,
        suppress_keys: bool = False,
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
        suppress_keys: Boolean for determining whether to include keys in the
            returned string
        **kwargs: options passed through to the builtin function sorted

    Returns:
        A string with key_value_separator used to separate keys from values and
        items_separator used to separate items

    """

    return_value = items_separator
    last_record_number = len(data_items)
    for n, k in enumerate(sorted(data_items.keys(), **kwargs)):
        if not suppress_keys:
            return_value += str(k)
            return_value += key_value_separator
        return_value += str(data_items[k])
        if n < last_record_number - 1:
            return_value += items_separator

    return return_value
