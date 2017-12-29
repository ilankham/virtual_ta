"""Creates functions for mail merging from various data formats"""

from io import BytesIO, FileIO, StringIO, TextIOWrapper
from typing import BinaryIO, TextIO, Union

from jinja2 import Template
from ruamel.yaml import YAML

from .data_conversions import convert_csv_to_dict, convert_xlsx_to_dict

FileIO = Union[BinaryIO, BytesIO, FileIO, StringIO, TextIO, TextIOWrapper]


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
            from and contains an XLSX file with columns headers in its first
            row
        key: a column header from data_xlsx_fp, whose values should be used as
            key values in the dictionary generated
        worksheet: a worksheet name from data_xlsx_fp

    Returns:
        A dictionary keyed by the specified column and having as values the
        results of rendering the template against the row from the specified
        worksheet of the XLSX file corresponding to the key value

    """

    data_dict = convert_xlsx_to_dict(
        data_xlsx_fp,
        key=key,
        worksheet=worksheet
    )

    return_value = mail_merge_from_dict(template_fp, data_dict)

    return return_value


def mail_merge_from_yaml_file(
    template_fp: FileIO,
    data_yaml_fp: Union[FileIO, str],
) -> dict:

    yaml = YAML()
    data_dict = yaml.load(data_yaml_fp)

    for key in data_dict:
        data_dict[key]['yaml_file_main_key'] = key

    return_value = mail_merge_from_dict(template_fp, data_dict)

    return return_value
