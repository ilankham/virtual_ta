"""Creates unit tests for project using unittest module"""

from datetime import date, datetime, timedelta
from io import StringIO
from unittest import TestCase
from unittest.mock import patch, PropertyMock

import requests_mock

from virtual_ta import (
    BlackboardClass,
    convert_csv_to_dict,
    convert_csv_to_multimap,
    convert_xlsx_to_dict,
    convert_xlsx_to_yaml_calendar,
    mail_merge_from_csv_file,
    mail_merge_from_dict,
    mail_merge_from_xlsx_file,
    mail_merge_from_yaml_file,
    flatten_dict,
    SlackAccount,
)
from .xlsx_mock import XlsxMock


# noinspection SpellCheckingInspection
class TestDataConversions(TestCase):
    def test_convert_csv_to_dict(self):
        test_expectations = {
            "auser1": {
                "User_Name": "auser1",
                "First_Name": "a",
                "Last_Name": "user1",
            },
            "buser2": {
                "User_Name": "buser2",
                "First_Name": "b",
                "Last_Name": "user2",
            },
        }

        test_csv_entries = [
            "User_Name,First_Name,Last_Name",
            "auser1,a,user1",
            "buser2,b,user2"
        ]
        test_csv = StringIO("\n".join(test_csv_entries))
        test_results = convert_csv_to_dict(
            test_csv,
            key="User_Name",
        )

        self.assertEqual(test_expectations, test_results)

    def test_convert_xlsx_to_dict(self):
        test_expectations = {
            "auser1": {
                "User_Name": "auser1",
                "First_Name": "a",
                "Last_Name": "user1",
            },
            "buser2": {
                "User_Name": "buser2",
                "First_Name": "b",
                "Last_Name": "user2",
            },
        }

        test_xlsx_entries = [
            ["User_Name", "First_Name", "Last_Name"],
            ["auser1", "a", "user1"],
            ["buser2", "b", "user2"],
        ]
        test_workbook = XlsxMock()
        test_workbook.create_sheet('test0')
        test_worksheet = test_workbook.create_sheet('test1')
        test_workbook.load_data(test_worksheet, test_xlsx_entries)
        test_workbook.create_sheet('test2')
        test_results = convert_xlsx_to_dict(
            test_workbook.as_file,
            key="User_Name",
            worksheet='test1',
        )

        self.assertEqual(test_expectations, test_results)

    def test_flatten_dict_with_options_passed_through(self):
        test_expectations = "buser2b user2auser1a user1"

        test_dict = {
            "auser1": "a user1",
            "buser2": "b user2",
        }
        test_key_value_separator = ""
        test_items_separator = ""

        test_results = flatten_dict(
            test_dict,
            test_key_value_separator,
            test_items_separator,
            reverse=True
        )

        self.assertEqual(test_expectations, test_results)

    def test_flatten_dict_without_options_passed_through(self):
        test_expectations = "auser1a user1buser2b user2"

        test_dict = {
            "auser1": "a user1",
            "buser2": "b user2",
        }
        test_key_value_separator = ""
        test_items_separator = ""

        test_results = flatten_dict(
            test_dict,
            test_key_value_separator,
            test_items_separator,
        )

        self.assertEqual(test_expectations, test_results)

    def test_convert_xlsx_to_yaml_calendar_after_start_date(self):
        test_expectations_list = [
            "1:",
            "  Tuesday:",
            "    Date: 02JAN2018",
            "    Activities:",
            "    - Week 1 Activity 2",
            "    - Week 1 Activity 3",
            "  Wednesday:",
            "    Date: 03JAN2018",
            "    Activities:",
            "    - Week 1 Activity 4",
            "  Thursday:",
            "    Date: 04JAN2018",
            "    Activities:",
            "    - Week 1 Activity 5",
            "  Friday:",
            "    Date: 05JAN2018",
            "    Activities:",
            "    - Week 1 Activity 6",
            "  Saturday:",
            "    Date: 06JAN2018",
            "    Activities:",
            "    - Week 1 Activity 7",
            "  Sunday:",
            "    Date: 07JAN2018",
            "    Activities:",
            "    - Week 1 Activity 8",
            "3:",
            "  Tuesday:",
            "    Date: 16JAN2018",
            "    Activities:",
            "    - Week 3 Activity 1",
            "  Friday:",
            "    Date: 19JAN2018",
            "    Activities:",
            "    - Week 3 Activity 2",
            "    - Week 3 Activity 3",
            "",
        ]
        test_expectations = '\n'.join(test_expectations_list)

        test_start_date = date(2018, 1, 3)
        test_item_delimiter = '|'
        test_week_number_column = 'Week'
        test_worksheet_name = 'Assessments'
        test_xlsx_entries = [
            [
                "Week",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
            [
                "1",
                "",
                "Week 1 Activity 2|Week 1 Activity 3",
                "Week 1 Activity 4",
                "Week 1 Activity 5",
                "Week 1 Activity 6",
                "Week 1 Activity 7",
                "Week 1 Activity 8",
            ],
            [
                "3",
                "",
                "Week 3 Activity 1",
                "",
                "",
                "Week 3 Activity 2|Week 3 Activity 3",
                "",
                "",
            ],
        ]
        test_workbook = XlsxMock()
        test_workbook.create_sheet('test0')
        test_worksheet = test_workbook.create_sheet(test_worksheet_name)
        test_workbook.load_data(test_worksheet, test_xlsx_entries)
        test_workbook.create_sheet('test2')
        test_results = convert_xlsx_to_yaml_calendar(
            data_xlsx_fp=test_workbook.as_file,
            start_date=test_start_date,
            item_delimiter=test_item_delimiter,
            week_number_column=test_week_number_column,
            worksheet=test_worksheet_name,
        )

        self.assertEqual(test_expectations, test_results)

    def test_convert_xlsx_to_yaml_calendar_on_start_date(self):
        test_expectations_list = [
            "1:",
            "  Tuesday:",
            "    Date: 02JAN2018",
            "    Activities:",
            "    - Week 1 Activity 2",
            "    - Week 1 Activity 3",
            "  Wednesday:",
            "    Date: 03JAN2018",
            "    Activities:",
            "    - Week 1 Activity 4",
            "  Thursday:",
            "    Date: 04JAN2018",
            "    Activities:",
            "    - Week 1 Activity 5",
            "  Friday:",
            "    Date: 05JAN2018",
            "    Activities:",
            "    - Week 1 Activity 6",
            "  Saturday:",
            "    Date: 06JAN2018",
            "    Activities:",
            "    - Week 1 Activity 7",
            "  Sunday:",
            "    Date: 07JAN2018",
            "    Activities:",
            "    - Week 1 Activity 8",
            "3:",
            "  Tuesday:",
            "    Date: 16JAN2018",
            "    Activities:",
            "    - Week 3 Activity 1",
            "  Friday:",
            "    Date: 19JAN2018",
            "    Activities:",
            "    - Week 3 Activity 2",
            "    - Week 3 Activity 3",
            "",
        ]
        test_expectations = '\n'.join(test_expectations_list)

        test_start_date = date(2018, 1, 1)
        test_item_delimiter = '|'
        test_week_number_column = 'Week'
        test_worksheet_name = 'Assessments'
        test_xlsx_entries = [
            [
                "Week",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
            [
                "1",
                "",
                "Week 1 Activity 2|Week 1 Activity 3",
                "Week 1 Activity 4",
                "Week 1 Activity 5",
                "Week 1 Activity 6",
                "Week 1 Activity 7",
                "Week 1 Activity 8",
            ],
            [
                "3",
                "",
                "Week 3 Activity 1",
                "",
                "",
                "Week 3 Activity 2|Week 3 Activity 3",
                "",
                "",
            ],
        ]
        test_workbook = XlsxMock()
        test_workbook.create_sheet('test0')
        test_worksheet = test_workbook.create_sheet(test_worksheet_name)
        test_workbook.load_data(test_worksheet, test_xlsx_entries)
        test_workbook.create_sheet('test2')
        test_results = convert_xlsx_to_yaml_calendar(
            data_xlsx_fp=test_workbook.as_file,
            start_date=test_start_date,
            item_delimiter=test_item_delimiter,
            week_number_column=test_week_number_column,
            worksheet=test_worksheet_name,
        )

        self.assertEqual(test_expectations, test_results)

    def test_convert_xlsx_to_yaml_calendar_before_start_date(self):
        test_expectations_list = [
            "1:",
            "  Tuesday:",
            "    Date: 02JAN2018",
            "    Activities:",
            "    - Week 1 Activity 2",
            "    - Week 1 Activity 3",
            "  Wednesday:",
            "    Date: 03JAN2018",
            "    Activities:",
            "    - Week 1 Activity 4",
            "  Thursday:",
            "    Date: 04JAN2018",
            "    Activities:",
            "    - Week 1 Activity 5",
            "  Friday:",
            "    Date: 05JAN2018",
            "    Activities:",
            "    - Week 1 Activity 6",
            "  Saturday:",
            "    Date: 06JAN2018",
            "    Activities:",
            "    - Week 1 Activity 7",
            "  Sunday:",
            "    Date: 07JAN2018",
            "    Activities:",
            "    - Week 1 Activity 8",
            "3:",
            "  Tuesday:",
            "    Date: 16JAN2018",
            "    Activities:",
            "    - Week 3 Activity 1",
            "  Friday:",
            "    Date: 19JAN2018",
            "    Activities:",
            "    - Week 3 Activity 2",
            "    - Week 3 Activity 3",
            "",
        ]
        test_expectations = '\n'.join(test_expectations_list)

        test_start_date = date(2018, 1, 1)
        test_item_delimiter = '|'
        test_week_number_column = 'Week'
        test_worksheet_name = 'Assessments'
        test_xlsx_entries = [
            [
                "Week",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
            [
                "1",
                "",
                "Week 1 Activity 2|Week 1 Activity 3",
                "Week 1 Activity 4",
                "Week 1 Activity 5",
                "Week 1 Activity 6",
                "Week 1 Activity 7",
                "Week 1 Activity 8",
            ],
            [
                "3",
                "",
                "Week 3 Activity 1",
                "",
                "",
                "Week 3 Activity 2|Week 3 Activity 3",
                "",
                "",
            ],
        ]
        test_workbook = XlsxMock()
        test_workbook.create_sheet('test0')
        test_worksheet = test_workbook.create_sheet(test_worksheet_name)
        test_workbook.load_data(test_worksheet, test_xlsx_entries)
        test_workbook.create_sheet('test2')
        test_results = convert_xlsx_to_yaml_calendar(
            data_xlsx_fp=test_workbook.as_file,
            start_date=test_start_date,
            item_delimiter=test_item_delimiter,
            week_number_column=test_week_number_column,
            worksheet=test_worksheet_name,
        )

        self.assertEqual(test_expectations, test_results)

    def test_convert_csv_to_multimap(self):
        test_expectations = {
            "team-1": [
                "uuser1-virtual_ta_testing",
                "uuser4-virtual_ta_testing",
            ],
            "team-2": [
                "uuser2-virtual_ta_testing",
                "uuser3-virtual_ta_testing",
            ],
        }

        test_csv_entries = [
            "GitHub_User_Name,Team_Number",
            "uuser1-virtual_ta_testing,team-1",
            "uuser2-virtual_ta_testing,team-2",
            "uuser3-virtual_ta_testing,team-2",
            "uuser4-virtual_ta_testing,team-1",
        ]
        test_csv = StringIO("\n".join(test_csv_entries))
        test_key_column = 'Team_Number'
        test_values_column = 'GitHub_User_Name'
        test_results = convert_csv_to_multimap(
            test_csv,
            key_column=test_key_column,
            values_column=test_values_column,
            overwrite_values=False,
        )

        self.assertEqual(test_expectations, test_results)


# noinspection SpellCheckingInspection
class TestMailMerging(TestCase):
    def test_mail_merge_from_dict(self):
        test_expectations = {
            "auser1": "a user1",
            "buser2": "b user2",
        }

        test_template = StringIO('{{First_Name}} {{Last_Name}}')
        test_dict = {
            "auser1": {
                "User_Name": "auser1",
                "First_Name": "a",
                "Last_Name": "user1",
            },
            "buser2": {
                "User_Name": "buser2",
                "First_Name": "b",
                "Last_Name": "user2",
            },
        }
        test_results = mail_merge_from_dict(
            test_template,
            test_dict,
        )

        self.assertEqual(test_expectations, test_results)

    def test_mail_merge_from_csv_file_with_key(self):
        test_expectations = {
            "auser1": "a user1",
            "buser2": "b user2",
        }

        test_template = StringIO('{{First_Name}} {{Last_Name}}')
        test_csv_entries = [
            "User_Name,First_Name,Last_Name",
            "auser1,a,user1",
            "buser2,b,user2"
        ]
        test_csv = StringIO("\n".join(test_csv_entries))
        test_results = mail_merge_from_csv_file(
            test_template,
            test_csv,
            key="User_Name",
        )

        self.assertEqual(test_expectations, test_results)

    def test_mail_merge_from_csv_file_without_key(self):
        test_expectations = {
            "auser1": "a user1",
            "buser2": "b user2",
        }

        test_template = StringIO('{{First_Name}} {{Last_Name}}')
        test_csv_entries = [
            "User_Name,First_Name,Last_Name",
            "auser1,a,user1",
            "buser2,b,user2"
        ]
        test_csv = StringIO("\n".join(test_csv_entries))
        test_results = mail_merge_from_csv_file(
            test_template,
            test_csv,
        )

        self.assertEqual(test_expectations, test_results)

    def test_mail_merge_from_xlsx_file(self):
        test_expectations = {
            "auser1": "a user1",
            "buser2": "b user2",
        }

        test_template = StringIO('{{First_Name}} {{Last_Name}}')
        test_xlsx_entries = [
            ["User_Name", "First_Name", "Last_Name"],
            ["auser1", "a", "user1"],
            ["buser2", "b", "user2"],
        ]
        test_workbook = XlsxMock()
        test_workbook.create_sheet('test0')
        test_worksheet = test_workbook.create_sheet('test1')
        test_workbook.load_data(test_worksheet, test_xlsx_entries)
        test_workbook.create_sheet('test2')
        test_results = mail_merge_from_xlsx_file(
            test_template,
            test_workbook.as_file,
            key="User_Name",
            worksheet='test1',
        )

        self.assertEqual(test_expectations, test_results)

    def test_mail_merge_from_yaml_file(self):
        test_expectations = {
            1: "a user1",
            2: "b user2",
        }

        test_template = StringIO('{{First_Name}} {{Last_Name}}')
        test_yaml_entries = [
            "1:",
            "  First_Name: a",
            "  Last_Name: user1",
            "2:",
            "  First_Name: b",
            "  Last_Name: user2",
            "",
        ]
        test_yaml = '\n'.join(test_yaml_entries)
        test_results = mail_merge_from_yaml_file(
            test_template,
            test_yaml
        )

        self.assertEqual(test_expectations, test_results)


# noinspection SpellCheckingInspection
class TestSlackAccounts(TestCase):
    def test_slack_account_class_init(self):
        test_token = "Test Token Value"

        test_bot = SlackAccount(test_token)

        self.assertEqual(test_token, test_bot.api_token)

    def test_slack_account_set_api_token_from_file(self):
        test_token = "Test Token Value"

        test_fp = StringIO(test_token)
        test_bot = SlackAccount()
        test_bot.set_api_token_from_file(test_fp)

        self.assertEqual(test_token, test_bot.api_token)

    def test_slack_account_user_ids_property(self):
        test_response_user_ids = {
            'auser1': 'userid-auser1',
            'buser1': 'userid-buser1',
        }

        test_token = "Test Token Value"
        test_json_user_ids = [
            {'name': 'auser1', 'id': 'userid-auser1'},
            {'name': 'buser1', 'id': 'userid-buser1'}
        ]
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                "https://slack.com/api/users.list",
                request_headers={
                    "Authorization": f"Bearer {test_token}",
                    "Content-type": "application/json",
                },
                status_code=200,
                json={'members': test_json_user_ids},
            )

            test_bot = SlackAccount(test_token)

            self.assertEqual(test_response_user_ids, test_bot.user_ids)

    @patch('virtual_ta.SlackAccount.user_ids', new_callable=PropertyMock)
    def test_slack_account_user_dm_channels_property(self, mock_user_ids):
        mock_user_ids.return_value = {
            'auser1': 'userid-auser1',
            'buser1': 'userid-buser1'
        }

        test_response_dm_channels = {
            'auser1': 'dmid-auser1',
            'buser1': 'dmid-buser1',
        }

        test_token = "Test Token Value"
        test_json_dm_channels = [
            {'user': 'userid-auser1', 'id': 'dmid-auser1'},
            {'user': 'userid-buser1', 'id': 'dmid-buser1'}
        ]
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                "https://slack.com/api/im.list",
                request_headers={
                    "Authorization": f"Bearer {test_token}",
                    "Content-type": "application/json",
                },
                status_code=200,
                json={'ims': test_json_dm_channels},
            )

            test_bot = SlackAccount(test_token)

            self.assertEqual(
                test_response_dm_channels,
                test_bot.user_dm_channels
            )

    @patch(
        'virtual_ta.SlackAccount.user_dm_channels',
        new_callable=PropertyMock
    )
    def test_slack_account_direct_message_by_username(
            self,
            mock_user_dm_channels
    ):
        mock_user_dm_channels.return_value = {
            'auser1': 'dmid-auser1',
            'buser1': 'dmid-buser1',
        }

        test_respond_dms = {
            'dmid-auser1': 'a user1',
            'dmid-buser1': 'b user1',
        }

        test_token = "Test Token Value"
        test_dms = {
            'auser1': 'a user1',
            'buser1': 'b user1',
        }
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                "https://slack.com/api/chat.postMessage",
                request_headers={
                    "Authorization": f"Bearer {test_token}",
                    "Content-type": "application/json",
                },
                status_code=200,
            )

            test_bot = SlackAccount(test_token)

            self.assertEqual(
                test_respond_dms,
                test_bot.direct_message_by_username(test_dms),
            )

        self.assertEqual(mock_requests.call_count, len(test_respond_dms))


# noinspection SpellCheckingInspection
class TestBlackboardClasses(TestCase):
    def test_bb_class_init(self):
        test_server_address = 'test.server.address'
        test_course_id = 'Test-Course-ID'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'

        test_bot = BlackboardClass(
            test_server_address,
            test_course_id,
            test_application_key,
            test_application_secret,
        )

        self.assertEqual(test_server_address, test_bot.server_address)
        self.assertEqual(test_course_id, test_bot.course_id)
        self.assertEqual(test_application_key, test_bot.application_key)
        self.assertEqual(test_application_secret, test_bot.application_secret)

    def test_bb_class_api_token_property_with_new_token(self):
        test_response_json = {
            'access_token': 'Test Token Value',
            'token_type': 'bearer',
            'expires_in': 3600,
        }

        test_server_address = 'test.server.address'
        test_course_id = 'Test-Course-ID'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                f'https://{test_server_address}/learn/api/public/v1/oauth2'
                f'/token',
                status_code=200,
                json=test_response_json,
            )

            test_bot = BlackboardClass(
                test_server_address,
                test_course_id,
                test_application_key,
                test_application_secret,
            )

            self.assertEqual(
                test_response_json['access_token'],
                test_bot.api_token,
            )

            test_api_token_expiration_datetime = (
                datetime.now() +
                timedelta(
                    seconds=test_response_json['expires_in']
                )
            )
            self.assertAlmostEqual(
                test_api_token_expiration_datetime.timestamp(),
                test_bot.api_token_expiration_datetime.timestamp(),
                places=0
            )

    def test_bb_class_api_token_property_with_old_token(self):
        test_response_json1 = {
            'access_token': 'Test Token Value',
            'token_type': 'bearer',
            'expires_in': 1,
        }
        test_response_json2 = {
            'access_token': 'Test Token Value',
            'token_type': 'bearer',
            'expires_in': 3600,
        }

        test_server_address = 'test.server.address'
        test_course_id = 'Test-Course-ID'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                f'https://{test_server_address}/learn/api/public/v1/oauth2'
                f'/token',
                [
                    {'json': test_response_json1, 'status_code': 200},
                    {'json': test_response_json2, 'status_code': 200},
                ]
            )

            test_bot = BlackboardClass(
                test_server_address,
                test_course_id,
                test_application_key,
                test_application_secret,
            )

            self.assertEqual(
                test_response_json2['access_token'],
                test_bot.api_token,
            )

            test_api_token_expiration_datetime = (
                    datetime.now() +
                    timedelta(
                        seconds=test_response_json2['expires_in']
                    )
            )
            self.assertAlmostEqual(
                test_api_token_expiration_datetime.timestamp(),
                test_bot.api_token_expiration_datetime.timestamp(),
                places=0
            )

    @patch('virtual_ta.BlackboardClass.api_token', new_callable=PropertyMock)
    def test_bb_class_create_gradebook_column(self, mock_api_token):
        mock_api_token.return_value = 'Test Token Value'

        test_column_name = 'Test Column Name'
        test_column_due_date = 'Test Column Due Date'
        test_response_json = {
            'availability': {'available': 'Yes'},
            'externalId': '',
            'grading': {
                'due': test_column_due_date,
                'type': 'Manual'
            },
            'name': test_column_name,
            'score': {'possible': 0.0}
        }

        test_server_address = 'test.server.address'
        test_course_id = 'Test-Course-ID'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                f'https://{test_server_address}/learn/api/public/v2/courses/'
                f'courseId:{test_course_id}/gradebook/columns',
                status_code=200,
                json=test_response_json,
            )

            test_bot = BlackboardClass(
                test_server_address,
                test_course_id,
                test_application_key,
                test_application_secret,
            )

            test_create_column_response = test_bot.create_gradebook_column(
                name=test_column_name,
                due_date=test_column_due_date,
            )

            self.assertEqual(
                test_response_json,
                test_create_column_response,
            )

    @patch('virtual_ta.BlackboardClass.api_token', new_callable=PropertyMock)
    def test_bb_class_gradebook_columns_property_without_paging(
        self,
        mock_api_token
    ):
        mock_api_token.return_value = 'Test Token Value'

        test_column_name = 'Test Column Name'
        test_column_due_date = 'Test Column Due Date'
        test_response_json = {
            'results': [
                {
                    'availability': {'available': 'Yes'},
                    'externalId': '',
                    'grading': {
                        'due': test_column_due_date,
                        'type': 'Manual'
                    },
                    'name': test_column_name,
                    'score': {'possible': 0.0},
                }
            ],
        }
        test_response = test_response_json['results']

        test_server_address = 'test.server.address'
        test_course_id = 'Test-Course-ID'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'

        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://{test_server_address}/learn/api/public/v2/courses/'
                f'courseId:{test_course_id}/gradebook/columns',
                status_code=200,
                json=test_response_json,
            )

            test_bot = BlackboardClass(
                test_server_address,
                test_course_id,
                test_application_key,
                test_application_secret,
            )

            self.assertEqual(
                test_response,
                list(test_bot.gradebook_columns),
            )

    @patch('virtual_ta.BlackboardClass.api_token', new_callable=PropertyMock)
    def test_bb_class_gradebook_columns_property_with_paging(
        self,
        mock_api_token
    ):
        mock_api_token.return_value = 'Test Token Value'

        test_server_address = 'test.server.address'
        test_course_id = 'Test-Course-ID'
        test_column_name1 = 'Test Column Name 1'
        test_column_due_date1 = 'Test Column Due Date 1'
        test_response_json1 = {
            'results': [
                {
                    'availability': {'available': 'Yes'},
                    'externalId': '',
                    'grading': {
                        'due': test_column_due_date1,
                        'type': 'Manual'
                    },
                    'name': test_column_name1,
                    'score': {'possible': 0.0},
                }
            ],
            'paging': {
                'nextPage':
                f'https://{test_server_address}/learn/api/public/v2/courses/'
                f'courseId:{test_course_id}/gradebook/columns?next=101',
            }
        }
        test_column_name2 = 'Test Column Name 2'
        test_column_due_date2 = 'Test Column Due Date 2'
        test_response_json2 = {
            'results': [
                {
                    'availability': {'available': 'Yes'},
                    'externalId': '',
                    'grading': {
                        'due': test_column_due_date2,
                        'type': 'Manual'
                    },
                    'name': test_column_name2,
                    'score': {'possible': 0.0},
                }
            ],
        }
        test_response = (
            test_response_json1['results'] +
            test_response_json2['results']
        )

        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'

        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://{test_server_address}/learn/api/public/v2/courses/'
                f'courseId:{test_course_id}/gradebook/columns',
                status_code=200,
                json=test_response_json1,
            )
            mock_requests.register_uri(
                'GET',
                f'https://{test_server_address}/learn/api/public/v2/courses/'
                f'courseId:{test_course_id}/gradebook/columns?next=101',
                status_code=200,
                json=test_response_json2,
            )

            test_bot = BlackboardClass(
                test_server_address,
                test_course_id,
                test_application_key,
                test_application_secret,
            )

            self.assertEqual(
                test_response,
                list(test_bot.gradebook_columns),
            )

    @patch('virtual_ta.BlackboardClass.api_token', new_callable=PropertyMock)
    @patch(
        'virtual_ta.BlackboardClass.gradebook_columns',
        new_callable=PropertyMock
    )
    def test_bb_class_gradebook_columns_primary_ids_property(
        self,
        mock_gradebook_columns,
        mock_api_token,
    ):
        mock_api_token.return_value = 'Test Token Value'

        test_column_name1 = 'Test Column Name 1'
        test_column_due_date1 = 'Test Column Due Date 1'
        test_column_primary_id1 = 'Test Primary ID 1'
        test_column_name2 = 'Test Column Name 2'
        test_column_due_date2 = 'Test Column Due Date 2'
        test_column_primary_id2 = 'Test Primary ID 2'
        mock_gradebook_columns.return_value = (
            {
                'availability': {'available': 'Yes'},
                'externalId': '',
                'grading': {
                    'due': test_column_due_date1,
                    'type': 'Manual'
                },
                'id': test_column_primary_id1,
                'name': test_column_name1,
                'score': {'possible': 0.0},
            },
            {
                'availability': {'available': 'Yes'},
                'externalId': '',
                'grading': {
                    'due': test_column_due_date2,
                    'type': 'Manual'
                },
                'id': test_column_primary_id2,
                'name': test_column_name2,
                'score': {'possible': 0.0},
            }
        )

        test_response = {
            test_column_name1: test_column_primary_id1,
            test_column_name2: test_column_primary_id2,
        }

        test_server_address = 'test.server.address'
        test_course_id = 'Test-Course-ID'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        test_bot = BlackboardClass(
            test_server_address,
            test_course_id,
            test_application_key,
            test_application_secret,
        )

        self.assertEqual(
            test_response,
            test_bot.gradebook_columns_primary_ids,
        )
