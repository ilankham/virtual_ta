from .blackboard_course import BlackboardCourse

from .data_conversions import (
    convert_csv_to_dict,
    convert_csv_to_multimap,
    convert_xlsx_to_dict,
    convert_xlsx_to_yaml_calendar,
    flatten_dict,
)

from .mail_merges import (
    mail_merge_from_csv_file,
    mail_merge_from_dict,
    mail_merge_from_xlsx_file,
    mail_merge_from_yaml_file,
)

from .slack_account import SlackAccount
