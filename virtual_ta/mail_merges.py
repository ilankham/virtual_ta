"""Creates functions for mail merging from various data formats"""

from collections import OrderedDict
from io import BytesIO, FileIO, StringIO, TextIOWrapper
from typing import BinaryIO, Dict, TextIO, Union

from jinja2 import Template
from ruamel.yaml import YAML

from .data_conversions import convert_csv_to_dict, convert_xlsx_to_dict

FileIO = Union[BinaryIO, BytesIO, FileIO, StringIO, TextIO, TextIOWrapper]


def mail_merge_from_dict(
    template_fp: FileIO,
    data_dict: dict,
) -> Dict[str, str]:
    """Mail merges a Jinja2 template against a dictionary of dictionaries

    This function inputs a Jinja2 template file and a dictionary of
    dictionaries, each having as keys variables in the template file, and
    outputs a dictionary with the same keys as the input dictionary and as
    values the results of rendering the template against the corresponding
    entry in the input dictionary

    Args:
        template_fp: pointer to text file or file-like object containing a
            Jinja2 template and ready to be read from
        data_dict: dictionary of dictionaries, with each inner-dictionary
            having as keys variables from the Jinja2 template

    Returns:
        A dictionary with the same keys as the input dictionary and as values
        the results of rendering the Jinja2 template against the corresponding
        entry in the input dictionary

    """

    template_text = Template(template_fp.read())

    return_value = OrderedDict()
    for k in data_dict:
        return_value[k] = template_text.render(data_dict[k])

    return return_value


def mail_merge_from_csv_file(
    template_fp: FileIO,
    data_csv_fp: FileIO,
    *,
    key: str = None,
) -> Dict[str, str]:
    """Mail merges a Jinja2 template against a CSV file

    This function inputs a Jinja2 template file, a CSV file, and a key column
    (defaulting to the left-most column, if not specified) and outputs a
    dictionary keyed by the specified column and having as values the results
    of rendering the Jinja2 template against the row from the CSV file
    corresponding to the key value

    Args:
        template_fp: pointer to text file or file-like object containing a
            Jinja2 template and ready to be read from
        data_csv_fp: pointer to CSV file or file-like object with columns
            headers in its first row and ready to be read from
        key: a column header from data_csv_fp, whose values should be used as
            keys in the dictionary generated

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
) -> Dict[str, str]:
    """Mail merges a Jinja2 template against an XLSX file

    This function inputs a Jinja2 template file, an XLSX file, a key column
    (defaulting to the left-most column, if not specified), and a worksheet
    name column (defaulting to the first worksheet, if not specified) and
    outputs a dictionary keyed by the specified column and having as values the
    results of rendering the template against the row from the specified
    worksheet of the XLSX file corresponding to the key value

    Args:
        template_fp: pointer to text file or file-like object containing a
            Jinja2 template and ready to be read from
        data_xlsx_fp: pointer to an XLSX file or file-like object with columns
            headers in its first row and ready to be read from
        key: a column header from data_xlsx_fp, whose values should be used as
            keys in the dictionary generated
        worksheet: a worksheet name from data_xlsx_fp, whose values should be
            used in the dictionary generated

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
) -> Dict[str, str]:
    """Mail merges a Jinja2 template against a YAML file

    This function inputs a Jinja2 template file and a YAML file representing
    a dictionary of dictionaries, each having as keys variables in the template
    file, and outputs a dictionary with the same keys as the input file and as
    values the results of rendering the template against the corresponding
    entry in the input file

    Args:
        template_fp: pointer to text file or file-like object containing a
            Jinja2 template and ready to be read from
        data_yaml_fp: pointer to YAML file or file-like object representing a
            dictionary of dictionaries, with each inner-dictionary having as
            keys variables from the Jinja2 template

    Returns:
        A dictionary with the same keys as the input file and as values the
        results of rendering the Jinja2 template against the corresponding
        entry in the input dictionary

    """

    yaml = YAML()
    data_dict = yaml.load(data_yaml_fp)

    for key in data_dict:
        data_dict[key]['yaml_file_main_key'] = key

    return_value = mail_merge_from_dict(template_fp, data_dict)

    return return_value
