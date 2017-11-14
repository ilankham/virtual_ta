from csv import DictReader

from jinja2 import Template


def render_template_from_csv_file(template_file, gradebook_file, *, key=None):
    template_text = Template(template_file.read())

    gradebook_file_reader = DictReader(gradebook_file)
    if key is None:
        key = gradebook_file_reader.fieldnames[0]

    return_value = {}
    for row in gradebook_file_reader:
        return_value[row[key]] = template_text.render(row)

    return return_value
