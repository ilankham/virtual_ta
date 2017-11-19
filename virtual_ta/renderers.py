from csv import DictReader
import typing

from jinja2 import Template


def render_template_from_csv_file(
    template_fp: typing.IO,
    gradebook_fp: typing.IO,
    *,
    key: str = None
) -> dict:
    template_text = Template(template_fp.read())

    gradebook_file_reader = DictReader(gradebook_fp)
    if key is None:
        key = gradebook_file_reader.fieldnames[0]

    return_value = {}
    for row in gradebook_file_reader:
        return_value[row[key]] = template_text.render(row)

    return return_value
