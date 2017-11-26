"""Creates unit tests for project using unittest module"""

from io import StringIO
from unittest import TestCase
from unittest.mock import patch, PropertyMock

import requests_mock

from virtual_ta import (
    mail_merge_from_dict,
    convert_csv_to_dict,
    convert_xlsx_to_dict,
    mail_merge_from_csv_file,
    mail_merge_from_xlsx_file,
    flatten_dict,
    SlackAccount,
)
from .xlsx_mock import XlsxMock


# noinspection SpellCheckingInspection
class TestDataConversions(TestCase):
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

        self.assertEqual(test_results, test_expectations)

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

        self.assertEqual(test_results, test_expectations)


# noinspection SpellCheckingInspection
class TestSlackAccounts(TestCase):
    def test_slack_bot_class_init(self):
        test_token = "Test Token Value"

        test_bot = SlackAccount(test_token)

        self.assertEqual(test_token, test_bot.api_token)

    def test_set_api_token_from_file(self):
        test_token = "Test Token Value"

        test_fp = StringIO(test_token)
        test_bot = SlackAccount()
        test_bot.set_api_token_from_file(test_fp)

        self.assertEqual(test_token, test_bot.api_token)

    def test_user_ids_property(self):
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
                json={'members': test_json_user_ids},
            )

            test_bot = SlackAccount(test_token)

            self.assertEqual(test_bot.user_ids, test_response_user_ids)

    @patch('virtual_ta.SlackAccount.user_ids', new_callable=PropertyMock)
    def test_user_dm_channels_property(self, mock_user_ids):
        mock_user_ids.return_value = {
            'auser1': 'userid-auser1',
            'buser1': 'userid-buser1'
        }

        test_token = "Test Token Value"
        test_json_dm_channels = [
            {'user': 'userid-auser1', 'id': 'dmid-auser1'},
            {'user': 'userid-buser1', 'id': 'dmid-buser1'}
        ]
        test_response_dm_channels = {
            'auser1': 'dmid-auser1',
            'buser1': 'dmid-buser1',
        }

        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                "https://slack.com/api/im.list",
                request_headers={
                    "Authorization": f"Bearer {test_token}",
                    "Content-type": "application/json",
                },
                json={'ims': test_json_dm_channels},
            )

            test_bot = SlackAccount(test_token)

            self.assertEqual(
                test_bot.user_dm_channels,
                test_response_dm_channels
            )

    @patch(
        'virtual_ta.SlackAccount.user_dm_channels',
        new_callable=PropertyMock
    )
    def test_direct_message_by_username(self, mock_user_dm_channels):
        mock_user_dm_channels.return_value = {
            'auser1': 'dmid-auser1',
            'buser1': 'dmid-buser1',
        }

        test_token = "Test Token Value"
        test_dms = {
            'auser1': 'a user1',
            'buser1': 'b user1',
        }
        test_respond_dms = {
            'dmid-auser1': 'a user1',
            'dmid-buser1': 'b user1',
        }

        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                "https://slack.com/api/chat.postMessage",
                request_headers={
                    "Authorization": f"Bearer {test_token}",
                    "Content-type": "application/json",
                },
            )

            test_bot = SlackAccount(test_token)
            self.assertEqual(
                test_bot.direct_message_by_username(test_dms),
                test_respond_dms
            )

        self.assertEqual(mock_requests.call_count, len(test_respond_dms))
