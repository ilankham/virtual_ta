"""Creates unit tests for project using unittest module"""

from datetime import date, datetime, timedelta
from io import StringIO
from unittest import TestCase
from unittest.mock import patch, PropertyMock

import requests_mock

from virtual_ta import (
    BlackboardCourse,
    convert_csv_to_dict,
    convert_csv_to_multimap,
    convert_xlsx_to_dict,
    convert_xlsx_to_yaml_calendar,
    flatten_dict,
    GitHubOrganization,
    mail_merge_from_csv_file,
    mail_merge_from_dict,
    mail_merge_from_xlsx_file,
    mail_merge_from_yaml_file,
    SlackAccount,
)
from .xlsx_mock import XlsxMock


# noinspection SpellCheckingInspection
class TestBlackboardCourses(TestCase):
    def test_bb_course_init_without_protocol(self):
        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'

        test_bot = BlackboardCourse(
            test_course_id,
            test_server_address,
            test_application_key,
            test_application_secret
        )

        self.assertEqual(test_course_id, test_bot.course_id)
        self.assertEqual(test_server_address, test_bot.server_address)
        self.assertEqual(test_application_key, test_bot.application_key)
        self.assertEqual(test_application_secret, test_bot.application_secret)

    def test_bb_course_init_with_protocol(self):
        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'

        test_bot = BlackboardCourse(
            test_course_id,
            'https://'+test_server_address,
            test_application_key,
            test_application_secret
        )

        self.assertEqual(test_course_id, test_bot.course_id)
        self.assertEqual(test_server_address, test_bot.server_address)
        self.assertEqual(test_application_key, test_bot.application_key)
        self.assertEqual(test_application_secret, test_bot.application_secret)

    def test_bb_course_repr(self):
        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'

        test_bot = BlackboardCourse(
            test_course_id,
            test_server_address,
            test_application_key,
            test_application_secret
        )

        self.assertIn(test_course_id, repr(test_bot))
        self.assertIn(test_server_address, repr(test_bot))

    def test_bb_course_api_token_property_with_new_token(self):
        test_response_json = {
            'access_token': 'Test Token Value',
            'token_type': 'bearer',
            'expires_in': 3600,
        }

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
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

            test_bot = BlackboardCourse(
                test_course_id,
                test_server_address,
                test_application_key,
                test_application_secret
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

    def test_bb_course_api_token_property_with_old_token(self):
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

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
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

            test_bot = BlackboardCourse(
                test_course_id,
                test_server_address,
                test_application_key,
                test_application_secret
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

    @patch('virtual_ta.BlackboardCourse.api_token', new_callable=PropertyMock)
    def test_bb_course_gradebook_columns_property_without_paging(
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

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns',
                status_code=200,
                json=test_response_json,
            )

            test_bot = BlackboardCourse(
                test_course_id,
                test_server_address,
                test_application_key,
                test_application_secret
            )

            self.assertEqual(
                test_response,
                list(test_bot.gradebook_columns),
            )

    @patch('virtual_ta.BlackboardCourse.api_token', new_callable=PropertyMock)
    def test_bb_course_gradebook_columns_property_with_paging(
        self,
        mock_api_token
    ):
        mock_api_token.return_value = 'Test Token Value'

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_column_name1 = 'Test Column Name 1'
        test_column_due_date1 = 'Test Column Due Date 1'
        test_response_json1 = {
            'results': [
                {
                    'availability': {'available': 'Yes'},
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
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns?next=101',
            }
        }
        test_column_name2 = 'Test Column Name 2'
        test_column_due_date2 = 'Test Column Due Date 2'
        test_response_json2 = {
            'results': [
                {
                    'availability': {'available': 'Yes'},
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
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns',
                status_code=200,
                json=test_response_json1,
            )
            mock_requests.register_uri(
                'GET',
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns?next=101',
                status_code=200,
                json=test_response_json2,
            )

            test_bot = BlackboardCourse(
                test_course_id,
                test_server_address,
                test_application_key,
                test_application_secret
            )

            self.assertEqual(
                test_response,
                list(test_bot.gradebook_columns),
            )

    @patch('virtual_ta.BlackboardCourse.api_token', new_callable=PropertyMock)
    @patch(
        'virtual_ta.BlackboardCourse.gradebook_columns',
        new_callable=PropertyMock
    )
    def test_bb_course_gradebook_columns_primary_ids_property(
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

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        test_bot = BlackboardCourse(
            test_course_id,
            test_server_address,
            test_application_key,
            test_application_secret
        )

        self.assertEqual(
            test_response,
            test_bot.gradebook_columns_primary_ids,
        )

    @patch('virtual_ta.BlackboardCourse.api_token', new_callable=PropertyMock)
    def test_bb_course_create_gradebook_column(self, mock_api_token):
        mock_api_token.return_value = 'Test Token Value'

        test_column_name = 'Test Column Name'
        test_column_due_date = 'Test Column Due Date'
        test_response_json = {
            'availability': {'available': 'Yes'},
            'grading': {
                'due': test_column_due_date,
                'type': 'Manual'
            },
            'name': test_column_name,
            'score': {'possible': 0.0}
        }

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns',
                status_code=200,
                json=test_response_json,
            )

            test_bot = BlackboardCourse(
                test_course_id,
                test_server_address,
                test_application_key,
                test_application_secret
            )
            test_create_column_response = test_bot.create_gradebook_column(
                name=test_column_name,
                due_date=test_column_due_date,
            )

            self.assertEqual(
                test_response_json,
                test_create_column_response,
            )

    @patch('virtual_ta.BlackboardCourse.api_token', new_callable=PropertyMock)
    def test_bb_course_get_user_primary_id(self, mock_api_token):
        mock_api_token.return_value = 'Test Token Value'

        test_response_json = {'userId': 'Test-User-ID'}

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        test_user_name = 'Test-User-Name'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://{test_server_address}/learn/api/public/v1/courses'
                f'/courseId:{test_course_id}/users/userName:{test_user_name}',
                status_code=200,
                json=test_response_json,
            )

            test_bot = BlackboardCourse(
                test_course_id,
                test_server_address,
                test_application_key,
                test_application_secret
            )

            self.assertEqual(
                test_response_json['userId'],
                test_bot.get_user_primary_id(test_user_name),
            )

    @patch('virtual_ta.BlackboardCourse.api_token', new_callable=PropertyMock)
    def test_bb_course_get_grade(self, mock_api_token):
        mock_api_token.return_value = 'Test Token Value'

        test_column_primary_id = 'Test-Primary-ID'
        test_grade_feedback = 'Test Grade Feedback'
        test_grade_as_score = 'Test Grade as Score'
        test_grade_as_text = 'Test Grade as Text'
        test_user_id = 'Test-User-ID'
        test_response_json = {
            'columnId': test_column_primary_id,
            'feedback': test_grade_feedback,
            'score': test_grade_as_score,
            'text': test_grade_as_text,
            'userId': test_user_id,
        }

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns'
                f'/{test_column_primary_id}/users'
                f'/userName:{test_user_id}',
                status_code=200,
                json=test_response_json,
            )

            test_bot = BlackboardCourse(
                test_course_id,
                test_server_address,
                test_application_key,
                test_application_secret
            )
            test_set_grade_response = test_bot.get_grade(
                column_primary_id=test_column_primary_id,
                user_name=test_user_id,
            )

            self.assertEqual(
                test_response_json,
                test_set_grade_response,
            )

    @patch('virtual_ta.BlackboardCourse.api_token', new_callable=PropertyMock)
    def test_bb_course_get_grades_in_column_without_paging(
        self,
        mock_api_token
    ):
        mock_api_token.return_value = 'Test Token Value'

        test_column_primary_id = 'Test-Primary-ID'
        test_grade_feedback1 = 'Test Grade Feedback 1'
        test_grade_as_score1 = 'Test Grade as Score 1'
        test_grade_as_text1 = 'Test Grade as Text 1'
        test_user_id1 = 'Test-User-ID1'
        test_response_json1 = {
            'columnId': test_column_primary_id,
            'feedback': test_grade_feedback1,
            'score': test_grade_as_score1,
            'text': test_grade_as_text1,
            'userId': test_user_id1,
        }
        test_grade_feedback2 = 'Test Grade Feedback 2'
        test_grade_as_score2 = 'Test Grade as Score 2'
        test_grade_as_text2 = 'Test Grade as Text 2'
        test_user_id2 = 'Test-User-ID2'
        test_response_json2 = {
            'columnId': test_column_primary_id,
            'feedback': test_grade_feedback2,
            'score': test_grade_as_score2,
            'text': test_grade_as_text2,
            'userId': test_user_id2,
        }
        test_response_json = {
            'results': [test_response_json1, test_response_json2]
        }

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns'
                f'/{test_column_primary_id}/users',
                status_code=200,
                json=test_response_json,
            )

            test_bot = BlackboardCourse(
                test_course_id,
                test_server_address,
                test_application_key,
                test_application_secret
            )

            self.assertEqual(
                test_response_json['results'],
                list(test_bot.get_grades_in_column(test_column_primary_id)),
            )

    @patch('virtual_ta.BlackboardCourse.api_token', new_callable=PropertyMock)
    def test_bb_course_get_grades_in_column_with_paging(self, mock_api_token):
        mock_api_token.return_value = 'Test Token Value'

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_column_primary_id = 'Test-Primary-ID'
        test_grade_feedback1 = 'Test Grade Feedback 1'
        test_grade_as_score1 = 'Test Grade as Score 1'
        test_grade_as_text1 = 'Test Grade as Text 1'
        test_user_id1 = 'Test-User-ID1'
        test_response_json1 = {
            'results': [
                {
                    'columnId': test_column_primary_id,
                    'feedback': test_grade_feedback1,
                    'score': test_grade_as_score1,
                    'text': test_grade_as_text1,
                    'userId': test_user_id1,
                }
            ],
            'paging': {
                'nextPage':
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns'
                f'/{test_column_primary_id}/users?next=101',
            }
        }
        test_grade_feedback2 = 'Test Grade Feedback 2'
        test_grade_as_score2 = 'Test Grade as Score 2'
        test_grade_as_text2 = 'Test Grade as Text 2'
        test_user_id2 = 'Test-User-ID2'
        test_response_json2 = {
            'results': [
                {
                    'columnId': test_column_primary_id,
                    'feedback': test_grade_feedback2,
                    'score': test_grade_as_score2,
                    'text': test_grade_as_text2,
                    'userId': test_user_id2,
                }
            ],
        }
        test_response = (
            test_response_json1['results'] + test_response_json2['results']
        )

        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns'
                f'/{test_column_primary_id}/users',
                status_code=200,
                json=test_response_json1,
            )
            mock_requests.register_uri(
                'GET',
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns'
                f'/{test_column_primary_id}/users?next=101',
                status_code=200,
                json=test_response_json2,
            )

            test_bot = BlackboardCourse(
                test_course_id,
                test_server_address,
                test_application_key,
                test_application_secret
            )

            self.assertEqual(
                test_response,
                list(test_bot.get_grades_in_column(test_column_primary_id)),
            )

    @patch('virtual_ta.BlackboardCourse.api_token', new_callable=PropertyMock)
    def test_bb_course_set_grade_with_overwrite(self, mock_api_token):
        mock_api_token.return_value = 'Test Token Value'

        test_column_primary_id = 'Test-Primary-ID'
        test_grade_feedback = 'Test Grade Feedback'
        test_grade_as_score = 'Test Grade as Score'
        test_grade_as_text = 'Test Grade as Text'
        test_user_id = 'Test-User-ID'
        test_response_json = {
            'columnId': test_column_primary_id,
            'feedback': test_grade_feedback,
            'score': test_grade_as_score,
            'text': test_grade_as_text,
            'userId': test_user_id,
        }

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'PATCH',
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns'
                f'/{test_column_primary_id}/users'
                f'/userName:{test_user_id}',
                status_code=200,
                json=test_response_json,
            )

            test_bot = BlackboardCourse(
                test_course_id,
                test_server_address,
                test_application_key,
                test_application_secret
            )
            test_set_grade_response = test_bot.set_grade(
                column_primary_id=test_column_primary_id,
                user_name=test_user_id,
                grade_as_score=test_grade_as_score,
                grade_as_text=test_grade_as_text,
                grade_feedback=test_grade_feedback,
                overwrite=True
            )

            self.assertEqual(
                test_response_json,
                test_set_grade_response,
            )

    @patch('virtual_ta.BlackboardCourse.api_token', new_callable=PropertyMock)
    def test_bb_course_set_grade_without_overwrite(self, mock_api_token):
        mock_api_token.return_value = 'Test Token Value'

        test_column_primary_id = 'Test-Primary-ID'
        test_user_id = 'Test-User-ID'
        test_grade_feedback1 = 'Test Grade Feedback 1'
        test_grade_as_score1 = 'Test Grade as Score 1'
        test_grade_as_text1 = 'Test Grade as Text 1'
        test_response_json1 = {
            'columnId': test_column_primary_id,
            'feedback': test_grade_feedback1,
            'score': test_grade_as_score1,
            'text': test_grade_as_text1,
            'userId': test_user_id,
        }
        test_grade_feedback2 = 'Test Grade Feedback 2'
        test_grade_as_score2 = 'Test Grade as Score 2'
        test_grade_as_text2 = 'Test Grade as Text 2'
        test_response_json2 = {
            'columnId': test_column_primary_id,
            'feedback': test_grade_feedback2,
            'score': test_grade_as_score2,
            'text': test_grade_as_text2,
            'userId': test_user_id,
        }

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'PATCH',
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns'
                f'/{test_column_primary_id}/users'
                f'/userName:{test_user_id}',
                [
                    {'json': test_response_json1, 'status_code': 200},
                    {'json': test_response_json2, 'status_code': 200},
                ]
            )
            mock_requests.register_uri(
                'GET',
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns'
                f'/{test_column_primary_id}/users'
                f'/userName:{test_user_id}',
                status_code=200,
                json=test_response_json1,
            )

            test_bot = BlackboardCourse(
                test_course_id,
                test_server_address,
                test_application_key,
                test_application_secret
            )
            test_bot.set_grade(
                column_primary_id=test_column_primary_id,
                user_name=test_user_id,
                grade_as_score=test_grade_as_score1,
                grade_as_text=test_grade_as_text1,
                grade_feedback=test_grade_feedback1,
                overwrite=False
            )
            test_set_grade_response = test_bot.set_grade(
                column_primary_id=test_column_primary_id,
                user_name=test_user_id,
                grade_as_score=test_grade_as_score2,
                grade_as_text=test_grade_as_text2,
                grade_feedback=test_grade_feedback2,
                overwrite=False
            )

            self.assertEqual(
                test_response_json1,
                test_set_grade_response,
            )

    @patch('virtual_ta.BlackboardCourse.api_token', new_callable=PropertyMock)
    def test_bb_course_set_grades_in_column(self, mock_api_token):
        mock_api_token.return_value = 'Test Token Value'

        test_column_primary_id = 'Test-Primary-ID'
        test_grade_feedback1 = 'Test Grade Feedback 1'
        test_grade_as_score1 = 'Test Grade as Score 1'
        test_grade_as_text1 = 'Test Grade as Text 1'
        test_user_id1 = 'Test-User-ID1'
        test_response_json1 = {
                'columnId': test_column_primary_id,
                'feedback': test_grade_feedback1,
                'score': test_grade_as_score1,
                'text': test_grade_as_text1,
                'userId': test_user_id1,
        }
        test_grade_feedback2 = 'Test Grade Feedback 2'
        test_grade_as_score2 = 'Test Grade as Score 2'
        test_grade_as_text2 = 'Test Grade as Text 2'
        test_user_id2 = 'Test-User-ID2'
        test_response_json2 = {
                'columnId': test_column_primary_id,
                'feedback': test_grade_feedback2,
                'score': test_grade_as_score2,
                'text': test_grade_as_text2,
                'userId': test_user_id2,
        }
        test_response = [test_response_json1, test_response_json2]

        test_course_id = 'Test-Course-ID'
        test_server_address = 'test.server.address'
        test_application_key = 'Test Application Key'
        test_application_secret = 'Test Application Secret'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'PATCH',
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns'
                f'/{test_column_primary_id}/users'
                f'/userName:{test_user_id1}',
                status_code=200,
                json=test_response_json1,
            )
            mock_requests.register_uri(
                'PATCH',
                f'https://{test_server_address}/learn/api/public/v2/courses'
                f'/courseId:{test_course_id}/gradebook/columns'
                f'/{test_column_primary_id}/users'
                f'/userName:{test_user_id2}',
                status_code=200,
                json=test_response_json2,
            )

            test_bot = BlackboardCourse(
                test_course_id,
                test_server_address,
                test_application_key,
                test_application_secret
            )
            test_update_gradebook_response = test_bot.set_grades_in_column(
                column_primary_id=test_column_primary_id,
                grades_as_scores={
                    test_user_id1: test_grade_as_score1,
                    test_user_id2: test_grade_as_score2,
                },
                grades_as_text={
                    test_user_id1: test_grade_as_text1,
                    test_user_id2: test_grade_as_text2,
                },
                grades_feedback={
                    test_user_id1: test_grade_feedback1,
                    test_user_id2: test_grade_feedback2,
                },
            )

            self.assertEqual(
                test_response,
                list(test_update_gradebook_response),
            )


# noinspection SpellCheckingInspection
class TestGitHubOrganizations(TestCase):
    def test_github_org_init(self):
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'

        test_bot = GitHubOrganization(
            test_org_name,
            test_personal_access_token,
        )

        self.assertEqual(test_org_name, test_bot.org_name)
        self.assertEqual(
            test_personal_access_token,
            test_bot.personal_access_token
        )

    def test_github_org_repr(self):
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'

        test_bot = GitHubOrganization(
            test_org_name,
            test_personal_access_token,
        )

        self.assertIn(test_org_name, repr(test_bot))

    def test_github_org_teams_property_without_paging(self):
        test_team_name = 'Test Team Name'
        test_team_id = 'Test Team ID'
        test_team_description = 'Test Team Description'
        test_response_json = {
            'name': test_team_name,
            'id': test_team_id,
            'description': test_team_description,
        }
        test_response = [test_response_json]

        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/orgs/{test_org_name}/teams',
                status_code=200,
                json=test_response,
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )

            self.assertEqual(
                test_response,
                list(test_bot.org_teams),
            )

    def test_github_org_teams_property_with_paging(self):
        test_team_name1 = 'Test Team Name 1'
        test_team_id1 = 'Test Team ID 1'
        test_team_description1 = 'Test Team Description 1'
        test_response_json1 = {
            'name': test_team_name1,
            'id': test_team_id1,
            'description': test_team_description1,
        }
        test_team_name2 = 'Test Team Name 2'
        test_team_id2 = 'Test Team ID 2'
        test_team_description2 = 'Test Team Description 2'
        test_response_json2 = {
            'name': test_team_name2,
            'id': test_team_id2,
            'description': test_team_description2,
        }
        test_response = [
            test_response_json1,
            test_response_json2
        ]

        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/orgs/{test_org_name}/teams',
                headers={
                    'Link':
                        f'<https://api.github.com/organizations'
                        f'/{test_org_name}/teams?page=2>; rel="next"'
                },
                status_code=200,
                json=[test_response_json1],
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/organizations/{test_org_name}/'
                f'teams?page=2',
                status_code=200,
                json=[test_response_json2],
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )

            self.assertEqual(
                test_response,
                list(test_bot.org_teams),
            )

    @patch(
        'virtual_ta.GitHubOrganization.org_teams',
        new_callable=PropertyMock
    )
    def test_github_org_team_ids_property(self, mock_org_teams):
        test_team_name1 = 'Test Team Name 1'
        test_team_id1 = 'Test Team ID 1'
        test_team_description1 = 'Test Team Description 1'
        test_team_name2 = 'Test Team Name 2'
        test_team_id2 = 'Test Team ID 2'
        test_team_description2 = 'Test Team Description 2'
        mock_org_teams.return_value = [
            {
                'name': test_team_name1,
                'id': test_team_id1,
                'description': test_team_description1,
            },
            {
                'name': test_team_name2,
                'id': test_team_id2,
                'description': test_team_description2,
            }
        ]

        test_response = {
            test_team_name1: test_team_id1,
            test_team_name2: test_team_id2,
        }

        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        test_bot = GitHubOrganization(
            test_org_name,
            test_personal_access_token,
        )

        self.assertEqual(
            test_response,
            test_bot.org_team_ids,
        )

    def test_github_org_create_org_team(self):
        test_team_name = 'Test Team Name'
        test_team_id = 'Test Team ID'
        test_team_description = 'Test Team Description'
        team_team_privacy = 'Test Team Privacy Setting'
        test_response_json = {
            'name': test_team_name,
            'id': test_team_id,
            'description': test_team_description,
            'privacy': team_team_privacy,
        }

        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                f'https://api.github.com/orgs/{test_org_name}/teams',
                status_code=200,
                json=test_response_json,
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )
            test_create_org_team_results = test_bot.create_org_team(
                team_name=test_team_name,
                team_description=test_team_description,
                team_privacy=team_team_privacy,
            )

            self.assertEqual(
                test_response_json,
                test_create_org_team_results,
            )

    def test_github_org_get_team_membership_without_paging(self):
        test_user_id = 'Test User ID'
        test_user_name = 'Test User Name'
        test_response_json = {
            'id': test_user_id,
            'login': test_user_name,
        }
        test_response = [test_response_json]

        test_team_id = 'Test-Team-ID'
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/teams/{test_team_id}/members',
                status_code=200,
                json=test_response,
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )

            self.assertEqual(
                test_response,
                list(test_bot.get_team_membership(test_team_id)),
            )

    def test_github_org_get_team_membership_with_paging(self):
        test_user_id1 = 'Test User ID 1'
        test_user_name1 = 'Test User Name 1'
        test_response_json1 = {
            'id': test_user_id1,
            'login': test_user_name1,
        }
        test_user_id2 = 'Test User ID 2'
        test_user_name2 = 'Test User Name 2'
        test_response_json2 = {
            'id': test_user_id2,
            'login': test_user_name2,
        }
        test_response = [
            test_response_json1,
            test_response_json2
        ]

        test_team_id = 'Test-Team-ID'
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/teams/{test_team_id}/members',
                headers={
                    'Link':
                        f'<https://api.github.com/teams/{test_team_id}'
                        f'/memberz?page=2>; rel="next"'
                },
                status_code=200,
                json=[test_response_json1],
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/teams/{test_team_id}/memberz?page=2',
                status_code=200,
                json=[test_response_json2],
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )

            self.assertEqual(
                test_response,
                list(test_bot.get_team_membership(test_team_id)),
            )

    def test_github_org_set_team_membership(self):
        test_user_name = 'Test-User-Name'
        test_user_role = 'Test User Role'
        test_response_json = {
            'role': test_user_role,
        }

        test_team_id = 'Test-Team-ID'
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'PUT',
                f'https://api.github.com/teams/{test_team_id}/memberships'
                f'/{test_user_name}',
                status_code=200,
                json=test_response_json,
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )
            test_set_team_membership_response = test_bot.set_team_membership(
                team_id=test_team_id,
                user_name=test_user_name,
                team_role=test_user_name,
            )

            self.assertEqual(
                test_response_json,
                test_set_team_membership_response,
            )

    def test_github_org_create_org_repo(self):
        test_repo_name = 'Test Repo Name'
        test_repo_id = 'Test Repo ID'
        test_repo_description = 'Test Repo Description'
        test_response_json = {
            'description': test_repo_description,
            'id': test_repo_id,
            'name': test_repo_name,
        }

        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                f'https://api.github.com/orgs/{test_org_name}/repos',
                status_code=200,
                json=test_response_json,
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )
            test_create_org_repo_response = test_bot.create_org_repo(
                repo_name=test_repo_name,
                repo_description=test_repo_description,
            )

            self.assertEqual(
                test_response_json,
                test_create_org_repo_response,
            )

    def test_github_org_get_repo_teams_without_paging(self):
        test_team_description = 'Test Team Description'
        test_team_id = 'Test Team ID'
        test_team_name = 'Test Team Name'
        test_response_json = {
            'description': test_team_description,
            'id': test_team_id,
            'name': test_team_name,
        }
        test_response = [test_response_json]

        test_repo_name = 'Test-Repo-Name'
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/teams',
                status_code=200,
                json=test_response,
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )

            self.assertEqual(
                test_response,
                list(test_bot.get_repo_teams(test_repo_name)),
            )

    def test_github_org_get_repo_teams_with_paging(self):
        test_team_description1 = 'Test Team Description 1'
        test_team_id1 = 'Test Team ID 1'
        test_team_name1 = 'Test Team Name 1'
        test_response_json1 = {
            'description': test_team_description1,
            'id': test_team_id1,
            'name': test_team_name1,
        }
        test_team_description2 = 'Test Team Description 2'
        test_team_id2 = 'Test Team ID 2'
        test_team_name2 = 'Test Team Name 2'
        test_response_json2 = {
            'description': test_team_description2,
            'id': test_team_id2,
            'name': test_team_name2,
        }
        test_response = [
            test_response_json1,
            test_response_json2
        ]

        test_repo_name = 'Test-Repo-Name'
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/teams',
                headers={
                    'Link':
                        f'<https://api.github.com/repos/{test_org_name}'
                        f'/{test_repo_name}/teamz?page=2>; rel="next"'
                },
                status_code=200,
                json=[test_response_json1],
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/teamz?page=2',
                status_code=200,
                json=[test_response_json2],
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )

            self.assertEqual(
                test_response,
                list(test_bot.get_repo_teams(test_repo_name)),
            )

    @patch('virtual_ta.GitHubOrganization.get_repo_teams')
    def test_github_org_set_repo_team(self, mock_get_repo_teams):
        test_team_description = 'Test Team Description'
        test_team_id = 'Test-Team-ID'
        test_team_name = 'Test Team Name'
        test_response_json = {
            'description': test_team_description,
            'id': test_team_id,
            'name': test_team_name,
        }
        mock_get_repo_teams.return_value = [test_response_json]

        test_repo_name = 'Test-Repo-Name'
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'PUT',
                f'https://api.github.com/teams/{test_team_id}/repos'
                f'/{test_org_name}/{test_repo_name}',
                status_code=204,
                json=test_response_json,
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )
            test_set_repo_team_response = test_bot.set_repo_team(
                repo_name=test_repo_name,
                team_id=test_team_id,
            )

            self.assertEqual(
                test_response_json,
                test_set_repo_team_response,
            )

    @patch('virtual_ta.GitHubOrganization.create_org_repo')
    @patch('virtual_ta.GitHubOrganization.set_repo_team')
    def test_github_org_create_team_repo(
        self,
        mock_set_repo_team,
        mock_create_org_repo,
    ):
        test_team_description = 'Test Team Description'
        test_team_id = 'Test-Team-ID'
        test_team_name = 'Test Team Name'
        test_response_json = {
            'description': test_team_description,
            'id': test_team_id,
            'name': test_team_name,
        }
        mock_set_repo_team.return_value = test_response_json

        test_repo_name = 'Test Repo Name'
        test_repo_id = 'Test Repo ID'
        test_repo_description = 'Test Repo Description'
        mock_create_org_repo.return_value = {
            'description': test_repo_description,
            'id': test_repo_id,
            'name': test_repo_name,
        }

        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        test_bot = GitHubOrganization(
            test_org_name,
            test_personal_access_token,
        )
        test_create_team_repo_response = test_bot.create_team_repo(
            repo_name=test_repo_name,
            team_id=test_team_id,
            repo_description=test_repo_description,
        )

        self.assertEqual(
            test_response_json,
            test_create_team_repo_response,
        )

    def test_github_org_remove_single_file_pr_deletions(self):
        test_expectations = [
            'Line 0',
            'Line 1',
            '',
            '',
            '',
            'Line 2',
            'Line 3',
            'Line 3 trailer',
            '',
            '',
            '',
            'Line 4',
            'Line 4 trailer',
            'Line 5',
            '',
            '',
            '',
            'Line 6',
            'Line 7',
            'Line 7 trailer',
            '',
            '',
            '',
            'Line 8',
            'Line 9',
            'Line 9 trailer',
            '',
            '',
            '',
        ]
        test_expectations_str = '\n'.join(test_expectations)

        test_pr_details_base_ref = 'Test-PR-Details-Base-Ref'
        test_pr_details_response_json = {
            'base': {
                'ref': test_pr_details_base_ref,
            },
            'changed_files': 1,
        }
        test_pr_details_raw_url = 'https://mock/test_pr_details_raw_url'
        test_pr_file_changes_response_json = [{
            'raw_url': test_pr_details_raw_url,
        }]
        test_pr_file_contents = [
            'Line 0',
            'Line 1',
            '',
            '',
            '',
            'Line 2',
            'Line 3',
            'Line 3 trailer',
            '',
            '',
            '',
            'Line 4',
            'Line 4 trailer',
            'Line 5',
            '',
            '',
            '',
            'Line 6',
            'Line 7',
            '',
            'Line 7 trailer',
            '',
            '',
            'Line 8',
            'Line 9 trailer',
            '',
            '',
            '',
        ]
        test_pr_file_contents_text = '\n'.join(test_pr_file_contents)
        test_base_file_contents = [
            'Line 0',
            'Line 1',
            '',
            '',
            '',
            'Line 2',
            'Line 3',
            '',
            '',
            '',
            'Line 4',
            'Line 5',
            '',
            '',
            '',
            'Line 6',
            'Line 7',
            '',
            '',
            '',
            'Line 8',
            'Line 9',
            '',
            '',
            '',
        ]
        test_base_file_contents_text = '\n'.join(test_base_file_contents)

        test_repo_name = 'Test-Repo-Name'
        test_pr_number = 'Test-PR-Number'
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls/{test_pr_number}',
                status_code=200,
                json=test_pr_details_response_json,
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls/{test_pr_number}/files',
                status_code=200,
                json=test_pr_file_changes_response_json,
            )
            mock_requests.register_uri(
                'GET',
                test_pr_details_raw_url,
                status_code=200,
                text=test_pr_file_contents_text,
            )
            mock_requests.register_uri(
                'GET',
                f'https://raw.githubusercontent.com/{test_org_name}'
                f'/{test_repo_name}/{test_pr_details_base_ref}'
                f'/{"/".join(test_pr_details_raw_url.split("/")[-2:])}',
                status_code=200,
                text=test_base_file_contents_text,
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )

            test_method_response = test_bot.remove_single_file_pr_deletions(
                repo_name=test_repo_name,
                pr_number=test_pr_number,
            )

            self.assertEqual(
                test_expectations_str,
                test_method_response,
            )

    def test_github_org_summarize_prs_by_author_without_paging(self):
        test_pr_author1 = "Test PR Author 1"
        test_pr_number1a = "Test-PR-Number-1a"
        test_pr_title1a = "Test PR Title 1a"
        test_pr_files_changed1a = "Test PR Files Changed 1a"
        test_pr_number1b = "Test-PR-Number-1b"
        test_pr_title1b = "Test PR Title 1b"
        test_pr_files_changed1b = "Test PR Files Changed 1b"
        test_pr_author2 = "Test PR Author 2"
        test_pr_number2a = "Test-PR-Number-2a"
        test_pr_title2a = "Test PR Title 2a"
        test_pr_files_changed2a = "Test PR Files Changed 2a"
        test_pr_number2b = "Test-PR-Number-2b"
        test_pr_title2b = "Test PR Title 2b"
        test_pr_files_changed2b = "Test PR Files Changed 2b"
        test_expectations = {
            test_pr_author1: [
                f'PR {test_pr_number1a}: {test_pr_title1a} '
                f'(files changed: {test_pr_files_changed1a})',
                f'PR {test_pr_number1b}: {test_pr_title1b} '
                f'(files changed: {test_pr_files_changed1b})',
            ],
            test_pr_author2: [
                f'PR {test_pr_number2a}: {test_pr_title2a} (files changed: '
                f'{test_pr_files_changed2a})',
                f'PR {test_pr_number2b}: {test_pr_title2b} (files changed: '
                f'{test_pr_files_changed2b})',
            ],
        }

        test_prs_response_json = [
            {
                 'number': test_pr_number1a,
                 'title': test_pr_title1a,
                 'user': {
                     'login': test_pr_author1,
                 },
            },
            {
                 'number': test_pr_number1b,
                 'title': test_pr_title1b,
                 'user': {
                     'login': test_pr_author1,
                 },
            },
            {
                 'number': test_pr_number2a,
                 'title': test_pr_title2a,
                 'user': {
                     'login': test_pr_author2,
                 },
            },
            {
                 'number': test_pr_number2b,
                 'title': test_pr_title2b,
                 'user': {
                     'login': test_pr_author2,
                 },
            },

        ]

        test_pr1a_response_json = {
                'number': test_pr_number1a,
                'title': test_pr_title1a,
                'user': {
                     'login': test_pr_author1,
                 },
                'changed_files': test_pr_files_changed1a,
        }

        test_pr1b_response_json = {
                'number': test_pr_number1b,
                'title': test_pr_title1b,
                'user': {
                     'login': test_pr_author1,
                 },
                'changed_files': test_pr_files_changed1b,
        }

        test_pr2a_response_json = {
                'number': test_pr_number2a,
                'title': test_pr_title2a,
                'user': {
                     'login': test_pr_author1,
                 },
                'changed_files': test_pr_files_changed2a,
        }

        test_pr2b_response_json = {
                'number': test_pr_number2b,
                'title': test_pr_title2b,
                'user': {
                     'login': test_pr_author1,
                 },
                'changed_files': test_pr_files_changed2b,
        }

        test_repo_name = 'Test-Repo-Name'
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls',
                status_code=200,
                json=test_prs_response_json,
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls/{test_pr_number1a}',
                status_code=200,
                json=test_pr1a_response_json,
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls/{test_pr_number1b}',
                status_code=200,
                json=test_pr1b_response_json,
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls/{test_pr_number2a}',
                status_code=200,
                json=test_pr2a_response_json,
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls/{test_pr_number2b}',
                status_code=200,
                json=test_pr2b_response_json,
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )

            test_method_response = test_bot.summarize_prs_by_author(
                repo_name=test_repo_name,
            )

            self.assertEqual(
                test_expectations,
                test_method_response,
            )

    def test_github_org_summarize_prs_by_author_with_paging(self):
        test_pr_author1 = "Test PR Author 1"
        test_pr_number1a = "Test-PR-Number-1a"
        test_pr_title1a = "Test PR Title 1a"
        test_pr_files_changed1a = "Test PR Files Changed 1a"
        test_pr_number1b = "Test-PR-Number-1b"
        test_pr_title1b = "Test PR Title 1b"
        test_pr_files_changed1b = "Test PR Files Changed 1b"
        test_pr_author2 = "Test PR Author 2"
        test_pr_number2a = "Test-PR-Number-2a"
        test_pr_title2a = "Test PR Title 2a"
        test_pr_files_changed2a = "Test PR Files Changed 2a"
        test_pr_number2b = "Test-PR-Number-2b"
        test_pr_title2b = "Test PR Title 2b"
        test_pr_files_changed2b = "Test PR Files Changed 2b"
        test_expectations = {
            test_pr_author1: [
                f'PR {test_pr_number1a}: {test_pr_title1a} '
                f'(files changed: {test_pr_files_changed1a})',
                f'PR {test_pr_number1b}: {test_pr_title1b} '
                f'(files changed: {test_pr_files_changed1b})',
            ],
            test_pr_author2: [
                f'PR {test_pr_number2a}: {test_pr_title2a} (files changed: '
                f'{test_pr_files_changed2a})',
                f'PR {test_pr_number2b}: {test_pr_title2b} (files changed: '
                f'{test_pr_files_changed2b})',
            ],
        }

        test_prs_response_json1 = [
            {
                 'number': test_pr_number1a,
                 'title': test_pr_title1a,
                 'user': {
                     'login': test_pr_author1,
                 },
            },
            {
                 'number': test_pr_number1b,
                 'title': test_pr_title1b,
                 'user': {
                     'login': test_pr_author1,
                 },
            },
        ]

        test_prs_response_json2 = [
            {
                 'number': test_pr_number2a,
                 'title': test_pr_title2a,
                 'user': {
                     'login': test_pr_author2,
                 },
            },
            {
                 'number': test_pr_number2b,
                 'title': test_pr_title2b,
                 'user': {
                     'login': test_pr_author2,
                 },
            },

        ]

        test_pr1a_response_json = {
                'number': test_pr_number1a,
                'title': test_pr_title1a,
                'user': {
                     'login': test_pr_author1,
                 },
                'changed_files': test_pr_files_changed1a,
        }

        test_pr1b_response_json = {
                'number': test_pr_number1b,
                'title': test_pr_title1b,
                'user': {
                     'login': test_pr_author1,
                 },
                'changed_files': test_pr_files_changed1b,
        }

        test_pr2a_response_json = {
                'number': test_pr_number2a,
                'title': test_pr_title2a,
                'user': {
                     'login': test_pr_author1,
                 },
                'changed_files': test_pr_files_changed2a,
        }

        test_pr2b_response_json = {
                'number': test_pr_number2b,
                'title': test_pr_title2b,
                'user': {
                     'login': test_pr_author1,
                 },
                'changed_files': test_pr_files_changed2b,
        }

        test_repo_name = 'Test-Repo-Name'
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls',
                headers={
                    'Link':
                        f'<https://api.github.com/repos/{test_org_name}'
                        f'/{test_repo_name}/pulls?page=2>; rel="next"'
                },
                status_code=200,
                json=test_prs_response_json1,
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls?page=2',
                status_code=200,
                json=test_prs_response_json2,
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls/{test_pr_number1a}',
                status_code=200,
                json=test_pr1a_response_json,
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls/{test_pr_number1b}',
                status_code=200,
                json=test_pr1b_response_json,
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls/{test_pr_number2a}',
                status_code=200,
                json=test_pr2a_response_json,
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls/{test_pr_number2b}',
                status_code=200,
                json=test_pr2b_response_json,
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )

            test_method_response = test_bot.summarize_prs_by_author(
                repo_name=test_repo_name,
            )

            self.assertEqual(
                test_expectations,
                test_method_response,
            )

    def test_github_org_get_pr_authors_without_paging(self):
        test_pr_author1 = "Test PR Author 1"
        test_pr_number1a = 1
        test_pr_title1a = "Test PR Title 1a"
        test_pr_number1b = 2
        test_pr_title1b = "Test PR Title 1b"
        test_pr_author2 = "Test PR Author 2"
        test_pr_number2a = 3
        test_pr_title2a = "Test PR Title 2a"
        test_pr_number2b = 4
        test_pr_title2b = "Test PR Title 2b"
        test_expectations = {
            test_pr_number1a: test_pr_author1,
            test_pr_number1b: test_pr_author1,
            test_pr_number2a: test_pr_author2,
            test_pr_number2b: test_pr_author2,
        }

        test_prs_response_json = [
            {
                 'number': test_pr_number1a,
                 'title': test_pr_title1a,
                 'user': {
                     'login': test_pr_author1,
                 },
            },
            {
                 'number': test_pr_number1b,
                 'title': test_pr_title1b,
                 'user': {
                     'login': test_pr_author1,
                 },
            },
            {
                 'number': test_pr_number2a,
                 'title': test_pr_title2a,
                 'user': {
                     'login': test_pr_author2,
                 },
            },
            {
                 'number': test_pr_number2b,
                 'title': test_pr_title2b,
                 'user': {
                     'login': test_pr_author2,
                 },
            },

        ]

        test_repo_name = 'Test-Repo-Name'
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls',
                status_code=200,
                json=test_prs_response_json,
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )

            test_method_response = test_bot.get_pr_authors(
                repo_name=test_repo_name,
            )

            self.assertEqual(
                test_expectations,
                test_method_response,
            )

    def test_github_org_get_pr_authors_with_paging(self):
        test_pr_author1 = "Test PR Author 1"
        test_pr_number1a = 1
        test_pr_title1a = "Test PR Title 1a"
        test_pr_number1b = 2
        test_pr_title1b = "Test PR Title 1b"
        test_pr_author2 = "Test PR Author 2"
        test_pr_number2a = 3
        test_pr_title2a = "Test PR Title 2a"
        test_pr_number2b = 4
        test_pr_title2b = "Test PR Title 2b"
        test_expectations = {
            test_pr_number1a: test_pr_author1,
            test_pr_number1b: test_pr_author1,
            test_pr_number2a: test_pr_author2,
            test_pr_number2b: test_pr_author2,
        }

        test_prs_response_json1 = [
            {
                 'number': test_pr_number1a,
                 'title': test_pr_title1a,
                 'user': {
                     'login': test_pr_author1,
                 },
            },
            {
                 'number': test_pr_number1b,
                 'title': test_pr_title1b,
                 'user': {
                     'login': test_pr_author1,
                 },
            },
        ]

        test_prs_response_json2 = [
            {
                 'number': test_pr_number2a,
                 'title': test_pr_title2a,
                 'user': {
                     'login': test_pr_author2,
                 },
            },
            {
                 'number': test_pr_number2b,
                 'title': test_pr_title2b,
                 'user': {
                     'login': test_pr_author2,
                 },
            },

        ]

        test_repo_name = 'Test-Repo-Name'
        test_org_name = 'Test-Org-Name'
        test_personal_access_token = 'Test Personal Access Token'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls',
                headers={
                    'Link':
                        f'<https://api.github.com/repos/{test_org_name}'
                        f'/{test_repo_name}/pulls?page=2>; rel="next"'
                },
                status_code=200,
                json=test_prs_response_json1,
            )
            mock_requests.register_uri(
                'GET',
                f'https://api.github.com/repos/{test_org_name}'
                f'/{test_repo_name}/pulls?page=2',
                status_code=200,
                json=test_prs_response_json2,
            )

            test_bot = GitHubOrganization(
                test_org_name,
                test_personal_access_token,
            )

            test_method_response = test_bot.get_pr_authors(
                repo_name=test_repo_name,
            )

            self.assertEqual(
                test_expectations,
                test_method_response,
            )


# noinspection SpellCheckingInspection
class TestDataConversions(TestCase):
    def test_convert_csv_to_dict(self):
        test_expectations = {
            'auser1': {
                'User_Name': 'auser1',
                'First_Name': 'a',
                'Last_Name': 'user1',
            },
            'buser2': {
                'User_Name': 'buser2',
                'First_Name': 'b',
                'Last_Name': 'user2',
            },
        }

        test_csv_entries = [
            'User_Name,First_Name,Last_Name',
            'auser1,a,user1',
            'buser2,b,user2'
        ]
        test_csv = StringIO('\n'.join(test_csv_entries))
        test_results = convert_csv_to_dict(
            test_csv,
            key='User_Name',
        )

        self.assertEqual(test_expectations, test_results)

    def test_convert_csv_to_multimap_without_overwrite(self):
        test_expectations = {
            'team-1': [
                'uuser1-virtual_ta_testing',
                'uuser4-virtual_ta_testing',
            ],
            'team-2': [
                'uuser2-virtual_ta_testing',
                'uuser3-virtual_ta_testing',
            ],
        }

        test_csv_entries = [
            'User_Name,Team_Number',
            'uuser1-virtual_ta_testing,team-1',
            'uuser2-virtual_ta_testing,team-2',
            'uuser3-virtual_ta_testing,team-2',
            'uuser4-virtual_ta_testing,team-1',
        ]
        test_csv = StringIO('\n'.join(test_csv_entries))
        test_key_column = 'Team_Number'
        test_values_column = 'User_Name'
        test_results = convert_csv_to_multimap(
            test_csv,
            key_column=test_key_column,
            values_column=test_values_column,
            overwrite_values=False,
        )

        self.assertEqual(test_expectations, test_results)

    def test_convert_csv_to_multimap_with_overwrite(self):
        test_expectations = {
            'team-1': 'uuser4-virtual_ta_testing',
            'team-2': 'uuser3-virtual_ta_testing',
        }

        test_csv_entries = [
            'User_Name,Team_Number',
            'uuser1-virtual_ta_testing,team-1',
            'uuser2-virtual_ta_testing,team-2',
            'uuser3-virtual_ta_testing,team-2',
            'uuser4-virtual_ta_testing,team-1',
        ]
        test_csv = StringIO('\n'.join(test_csv_entries))
        test_key_column = 'Team_Number'
        test_values_column = 'User_Name'
        test_results = convert_csv_to_multimap(
            test_csv,
            key_column=test_key_column,
            values_column=test_values_column,
            overwrite_values=True,
        )

        self.assertEqual(test_expectations, test_results)

    def test_convert_xlsx_to_dict(self):
        test_expectations = {
            'auser1': {
                'User_Name': 'auser1',
                'First_Name': 'a',
                'Last_Name': 'user1',
            },
            'buser2': {
                'User_Name': 'buser2',
                'First_Name': 'b',
                'Last_Name': 'user2',
            },
        }

        test_xlsx_entries = [
            ['User_Name', 'First_Name', 'Last_Name'],
            ['auser1', 'a', 'user1'],
            ['buser2', 'b', 'user2'],
        ]
        test_workbook = XlsxMock()
        test_workbook.create_sheet('test0')
        test_worksheet = test_workbook.create_sheet('test1')
        test_workbook.load_data(test_worksheet, test_xlsx_entries)
        test_workbook.create_sheet('test2')
        test_results = convert_xlsx_to_dict(
            test_workbook.as_file,
            key='User_Name',
            worksheet='test1',
        )

        self.assertEqual(test_expectations, test_results)

    def test_convert_xlsx_to_yaml_calendar_on_start_date(self):
        test_expectations_list = [
            '1:',
            '  Tuesday:',
            '    Date: 02JAN2018',
            '    Activities:',
            '    - Week 1 Activity 2',
            '    - Week 1 Activity 3',
            '  Wednesday:',
            '    Date: 03JAN2018',
            '    Activities:',
            '    - Week 1 Activity 4',
            '  Thursday:',
            '    Date: 04JAN2018',
            '    Activities:',
            '    - Week 1 Activity 5',
            '  Friday:',
            '    Date: 05JAN2018',
            '    Activities:',
            '    - Week 1 Activity 6',
            '  Saturday:',
            '    Date: 06JAN2018',
            '    Activities:',
            '    - Week 1 Activity 7',
            '  Sunday:',
            '    Date: 07JAN2018',
            '    Activities:',
            '    - Week 1 Activity 8',
            '3:',
            '  Tuesday:',
            '    Date: 16JAN2018',
            '    Activities:',
            '    - Week 3 Activity 1',
            '  Friday:',
            '    Date: 19JAN2018',
            '    Activities:',
            '    - Week 3 Activity 2',
            '    - Week 3 Activity 3',
            '',
        ]
        test_expectations = '\n'.join(test_expectations_list)

        test_start_date = date(2018, 1, 2)
        test_item_delimiter = '|'
        test_week_number_column = 'Week'
        test_worksheet_name = 'Assessments'
        test_xlsx_entries = [
            [
                'Week',
                'Monday',
                'Tuesday',
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday',
                'Sunday',
            ],
            [
                '1',
                '',
                'Week 1 Activity 2|Week 1 Activity 3',
                'Week 1 Activity 4',
                'Week 1 Activity 5',
                'Week 1 Activity 6',
                'Week 1 Activity 7',
                'Week 1 Activity 8',
            ],
            [
                '3',
                '',
                'Week 3 Activity 1',
                '',
                '',
                'Week 3 Activity 2|Week 3 Activity 3',
                '',
                '',
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
            relative_week_number_column=test_week_number_column,
            worksheet=test_worksheet_name,
        )

        self.assertEqual(test_expectations, test_results)

    def test_convert_xlsx_to_yaml_calendar_before_start_date(self):
        test_expectations_list = [
            '1:',
            '  Tuesday:',
            '    Date: 02JAN2018',
            '    Activities:',
            '    - Week 1 Activity 2',
            '    - Week 1 Activity 3',
            '  Wednesday:',
            '    Date: 03JAN2018',
            '    Activities:',
            '    - Week 1 Activity 4',
            '  Thursday:',
            '    Date: 04JAN2018',
            '    Activities:',
            '    - Week 1 Activity 5',
            '  Friday:',
            '    Date: 05JAN2018',
            '    Activities:',
            '    - Week 1 Activity 6',
            '  Saturday:',
            '    Date: 06JAN2018',
            '    Activities:',
            '    - Week 1 Activity 7',
            '  Sunday:',
            '    Date: 07JAN2018',
            '    Activities:',
            '    - Week 1 Activity 8',
            '3:',
            '  Tuesday:',
            '    Date: 16JAN2018',
            '    Activities:',
            '    - Week 3 Activity 1',
            '  Friday:',
            '    Date: 19JAN2018',
            '    Activities:',
            '    - Week 3 Activity 2',
            '    - Week 3 Activity 3',
            '',
        ]
        test_expectations = '\n'.join(test_expectations_list)

        test_start_date = date(2018, 1, 1)
        test_item_delimiter = '|'
        test_week_number_column = 'Week'
        test_worksheet_name = 'Assessments'
        test_xlsx_entries = [
            [
                'Week',
                'Monday',
                'Tuesday',
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday',
                'Sunday',
            ],
            [
                '1',
                '',
                'Week 1 Activity 2|Week 1 Activity 3',
                'Week 1 Activity 4',
                'Week 1 Activity 5',
                'Week 1 Activity 6',
                'Week 1 Activity 7',
                'Week 1 Activity 8',
            ],
            [
                '3',
                '',
                'Week 3 Activity 1',
                '',
                '',
                'Week 3 Activity 2|Week 3 Activity 3',
                '',
                '',
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
            relative_week_number_column=test_week_number_column,
            worksheet=test_worksheet_name,
        )

        self.assertEqual(test_expectations, test_results)

    def test_convert_xlsx_to_yaml_calendar_after_start_date(self):
        test_expectations_list = [
            '1:',
            '  Tuesday:',
            '    Date: 02JAN2018',
            '    Activities:',
            '    - Week 1 Activity 2',
            '    - Week 1 Activity 3',
            '  Wednesday:',
            '    Date: 03JAN2018',
            '    Activities:',
            '    - Week 1 Activity 4',
            '  Thursday:',
            '    Date: 04JAN2018',
            '    Activities:',
            '    - Week 1 Activity 5',
            '  Friday:',
            '    Date: 05JAN2018',
            '    Activities:',
            '    - Week 1 Activity 6',
            '  Saturday:',
            '    Date: 06JAN2018',
            '    Activities:',
            '    - Week 1 Activity 7',
            '  Sunday:',
            '    Date: 07JAN2018',
            '    Activities:',
            '    - Week 1 Activity 8',
            '3:',
            '  Tuesday:',
            '    Date: 16JAN2018',
            '    Activities:',
            '    - Week 3 Activity 1',
            '  Friday:',
            '    Date: 19JAN2018',
            '    Activities:',
            '    - Week 3 Activity 2',
            '    - Week 3 Activity 3',
            '',
        ]
        test_expectations = '\n'.join(test_expectations_list)

        test_start_date = date(2018, 1, 3)
        test_item_delimiter = '|'
        test_week_number_column = 'Week'
        test_worksheet_name = 'Assessments'
        test_xlsx_entries = [
            [
                'Week',
                'Monday',
                'Tuesday',
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday',
                'Sunday',
            ],
            [
                '1',
                '',
                'Week 1 Activity 2|Week 1 Activity 3',
                'Week 1 Activity 4',
                'Week 1 Activity 5',
                'Week 1 Activity 6',
                'Week 1 Activity 7',
                'Week 1 Activity 8',
            ],
            [
                '3',
                '',
                'Week 3 Activity 1',
                '',
                '',
                'Week 3 Activity 2|Week 3 Activity 3',
                '',
                '',
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
            relative_week_number_column=test_week_number_column,
            worksheet=test_worksheet_name,
        )

        self.assertEqual(test_expectations, test_results)

    def test_flatten_dict_with_options_passed_through(self):
        test_expectations = 'buser2b user2auser1a user1'

        test_dict = {
            'auser1': 'a user1',
            'buser2': 'b user2',
        }
        test_key_value_separator = ''
        test_items_separator = ''
        test_results = flatten_dict(
            test_dict,
            test_key_value_separator,
            test_items_separator,
            reverse=True
        )

        self.assertEqual(test_expectations, test_results)

    def test_flatten_dict_without_options_passed_through(self):
        test_expectations = 'auser1a user1buser2b user2'

        test_dict = {
            'auser1': 'a user1',
            'buser2': 'b user2',
        }
        test_key_value_separator = ''
        test_items_separator = ''
        test_results = flatten_dict(
            test_dict,
            test_key_value_separator,
            test_items_separator,
        )

        self.assertEqual(test_expectations, test_results)


# noinspection SpellCheckingInspection
class TestMailMerging(TestCase):
    def test_mail_merge_from_dict(self):
        test_expectations = {
            'auser1': 'a user1',
            'buser2': 'b user2',
        }

        test_template = StringIO('{{First_Name}} {{Last_Name}}')
        test_dict = {
            'auser1': {
                'User_Name': 'auser1',
                'First_Name': 'a',
                'Last_Name': 'user1',
            },
            'buser2': {
                'User_Name': 'buser2',
                'First_Name': 'b',
                'Last_Name': 'user2',
            },
        }
        test_results = mail_merge_from_dict(
            test_template,
            test_dict,
        )

        self.assertEqual(test_expectations, test_results)

    def test_mail_merge_from_csv_file(self):
        test_expectations = {
            'auser1': 'a user1',
            'buser2': 'b user2',
        }

        test_template = StringIO('{{First_Name}} {{Last_Name}}')
        test_csv_entries = [
            'User_Name,First_Name,Last_Name',
            'auser1,a,user1',
            'buser2,b,user2'
        ]
        test_csv = StringIO('\n'.join(test_csv_entries))
        test_results = mail_merge_from_csv_file(
            test_template,
            test_csv,
            key='User_Name',
        )

        self.assertEqual(test_expectations, test_results)

    def test_mail_merge_from_xlsx_file(self):
        test_expectations = {
            'auser1': 'a user1',
            'buser2': 'b user2',
        }

        test_template = StringIO('{{First_Name}} {{Last_Name}}')
        test_xlsx_entries = [
            ['User_Name', 'First_Name', 'Last_Name'],
            ['auser1', 'a', 'user1'],
            ['buser2', 'b', 'user2'],
        ]
        test_workbook = XlsxMock()
        test_workbook.create_sheet('test0')
        test_worksheet = test_workbook.create_sheet('test1')
        test_workbook.load_data(test_worksheet, test_xlsx_entries)
        test_workbook.create_sheet('test2')
        test_results = mail_merge_from_xlsx_file(
            test_template,
            test_workbook.as_file,
            key='User_Name',
            worksheet='test1',
        )

        self.assertEqual(test_expectations, test_results)

    def test_mail_merge_from_yaml_file(self):
        test_expectations = {
            1: 'a user1',
            2: 'b user2',
        }

        test_template = StringIO('{{First_Name}} {{Last_Name}}')
        test_yaml_entries = [
            '1:',
            '  First_Name: a',
            '  Last_Name: user1',
            '2:',
            '  First_Name: b',
            '  Last_Name: user2',
            '',
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
        test_token = 'Test Token Value'
        test_user_name = 'Test User Name'

        test_bot = SlackAccount(test_token, user_name=test_user_name)

        self.assertEqual(test_token, test_bot.api_token)
        self.assertEqual(test_user_name, test_bot.user_name)

    def test_slack_account_repr(self):
        test_token = 'Test Token Value'
        test_user_name = 'Test User Name'

        test_bot = SlackAccount(test_token, user_name=test_user_name)

        self.assertIn(test_user_name, repr(test_bot))

    def test_slack_account_user_ids_property(self):
        test_response_user_ids = {
            'auser1': 'userid-auser1',
            'buser1': 'userid-buser1',
        }

        test_token = 'Test Token Value'
        test_json_user_ids = [
            {'name': 'auser1', 'id': 'userid-auser1'},
            {'name': 'buser1', 'id': 'userid-buser1'}
        ]
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/users.list',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                    'Content-type': 'application/json',
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

        test_token = 'Test Token Value'
        test_json_dm_channels = [
            {'user': 'userid-auser1', 'id': 'dmid-auser1'},
            {'user': 'userid-buser1', 'id': 'dmid-buser1'}
        ]
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/im.list',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                    'Content-type': 'application/json',
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

        test_token = 'Test Token Value'
        test_dms = {
            'auser1': 'a user1',
            'buser1': 'b user1',
        }
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/chat.postMessage',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                    'Content-type': 'application/json',
                },
                status_code=200,
            )

            test_bot = SlackAccount(test_token)

            self.assertEqual(
                test_respond_dms,
                test_bot.direct_message_by_username(test_dms),
            )

        self.assertEqual(mock_requests.call_count, len(test_respond_dms))

    @patch(
        'virtual_ta.SlackAccount.user_dm_channels',
        new_callable=PropertyMock
    )
    def test_slack_account_get_most_recent_direct_messages(
            self,
            mock_user_dm_channels
    ):
        test_username = 'Test User Name'
        mock_user_dm_channels.return_value = {
            test_username: 'Test User DM Channel',
        }

        test_response_json = {
            'messages': [
                {
                    'text': 'Test Message',
                },
            ],
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/im.history',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                    'Content-type': 'application/x-www-form-urlencoded',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            test_method_response = test_bot.get_most_recent_direct_messages(
                username=test_username,
                message_count=1,
            )

            self.assertEqual(
                [test_response_json['messages'][0]['text']],
                list(test_method_response),
            )

    def test_slack_account_public_channels_property_without_paging(self):
        test_channel_name1 = 'Test Channel Name 1'
        test_channel_name2 = 'Test Channel Name 2'
        test_channel_id1 = 'Test Public Channel ID 1'
        test_channel_id2 = 'Test Public Channel ID 2'
        test_response_json = {
            'channels': [
                {
                    'name': test_channel_name1,
                    'id': test_channel_id1,
                },
                {
                    'name': test_channel_name2,
                    'id': test_channel_id2,
                },
            ],
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/channels.list',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            self.assertEqual(
                test_response_json['channels'],
                list(test_bot.public_channels),
            )

    def test_slack_account_public_channels_property_with_paging(self):
        test_channel_name1 = 'Test Channel Name 1'
        test_channel_name2 = 'Test Channel Name 2'
        test_channel_id1 = 'Test Public Channel ID 1'
        test_channel_id2 = 'Test Public Channel ID 2'
        test_cursor = 'Test Next Cursor'
        test_response_json1 = {
            'channels': [
                {
                    'name': test_channel_name1,
                    'id': test_channel_id1,
                },
            ],
            'response_metadata': {
                'next_cursor': test_cursor
            },
        }
        test_response_json2 = {
            'channels': [
                {
                    'name': test_channel_name2,
                    'id': test_channel_id2,
                },
            ],
        }

        test_expectations = [
            {
                'name': test_channel_name1,
                'id': test_channel_id1,
            },
            {
                'name': test_channel_name2,
                'id': test_channel_id2,
            },
        ]

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/channels.list',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                    'cursor': '',
                },
                status_code=200,
                json=test_response_json1,
            )
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/channels.list',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                    'cursor': test_cursor,
                },
                status_code=200,
                json=test_response_json2,
            )

            test_bot = SlackAccount(test_token)

            self.assertEqual(
                test_expectations,
                list(test_bot.public_channels),
            )

    @patch(
        'virtual_ta.SlackAccount.public_channels',
        new_callable=PropertyMock
    )
    def test_slack_account_public_channels_ids_property(
        self,
        mock_public_channels,
    ):
        test_channel_name1 = 'Test Channel Name 1'
        test_channel_name2 = 'Test Channel Name 2'
        test_channel_id1 = 'Test Public Channel ID 1'
        test_channel_id2 = 'Test Public Channel ID 2'
        mock_public_channels.return_value = [
            {
                'name': test_channel_name1,
                'id': test_channel_id1,
            },
            {
                'name': test_channel_name2,
                'id': test_channel_id2,
            },
        ]

        test_expectations = {
            test_channel_name1: test_channel_id1,
            test_channel_name2: test_channel_id2,
        }

        test_token = 'Test Token Value'

        test_bot = SlackAccount(test_token)

        self.assertEqual(
            test_expectations,
            test_bot.public_channels_ids,
        )

    def test_slack_account_private_channels_property(self):
        test_channel_name1 = 'Test Channel Name 1'
        test_channel_name2 = 'Test Channel Name 2'
        test_channel_id1 = 'Test Private Channel ID 1'
        test_channel_id2 = 'Test Private Channel ID 2'
        test_response_json = {
            'groups': [
                {
                    'name': test_channel_name1,
                    'id': test_channel_id1,
                },
                {
                    'name': test_channel_name2,
                    'id': test_channel_id2,
                },
            ],
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/groups.list',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            self.assertEqual(
                test_response_json['groups'],
                list(test_bot.private_channels),
            )

    @patch(
        'virtual_ta.SlackAccount.private_channels',
        new_callable=PropertyMock
    )
    def test_slack_account_private_channels_ids_property(
        self,
        mock_private_channels
    ):
        test_channel_name1 = 'Test Channel Name 1'
        test_channel_name2 = 'Test Channel Name 2'
        test_channel_id1 = 'Test Private Channel ID 1'
        test_channel_id2 = 'Test Private Channel ID 2'
        mock_private_channels.return_value = [
            {
                'name': test_channel_name1,
                'id': test_channel_id1,
            },
            {
                'name': test_channel_name2,
                'id': test_channel_id2,
            },
        ]

        test_expectations = {
            test_channel_name1: test_channel_id1,
            test_channel_name2: test_channel_id2,
        }

        test_token = 'Test Token Value'

        test_bot = SlackAccount(test_token)

        self.assertEqual(
            test_expectations,
            test_bot.private_channels_ids,
        )

    @patch(
        'virtual_ta.SlackAccount.public_channels_ids',
        new_callable=PropertyMock
    )
    def test_slack_account_get_public_channel_info(
            self,
            mock_public_channels_ids
    ):
        test_channel_name1 = 'test-channel-name-1'
        test_channel_name2 = 'test-channel-name-2'
        test_channel_id1 = 'Test Public Channel ID 1'
        test_channel_id2 = 'Test Public Channel ID 2'
        mock_public_channels_ids.return_value = {
            test_channel_name1: test_channel_id1,
            test_channel_name2: test_channel_id2,
        }

        test_response_json = {
            'group': {
                'id': test_channel_id1,
                'name': test_channel_name1,
            }
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/channels.info',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            test_method_response = test_bot.get_public_channel_info(
                channel_name=test_channel_name1,
            )

            self.assertEqual(
                test_response_json,
                test_method_response,
            )

    @patch(
        'virtual_ta.SlackAccount.private_channels_ids',
        new_callable=PropertyMock
    )
    def test_slack_account_get_private_channel_info(
            self,
            mock_private_channels_ids
    ):
        test_channel_name1 = 'test-channel-name-1'
        test_channel_name2 = 'test-channel-name-2'
        test_channel_id1 = 'Test Private Channel ID 1'
        test_channel_id2 = 'Test Private Channel ID 2'
        mock_private_channels_ids.return_value = {
            test_channel_name1: test_channel_id1,
            test_channel_name2: test_channel_id2,
        }

        test_response_json = {
            'group': {
                'id': test_channel_id1,
                'name': test_channel_name1,
            }
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/groups.info',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            test_method_response = test_bot.get_private_channel_info(
                channel_name=test_channel_name1,
            )

            self.assertEqual(
                test_response_json,
                test_method_response,
            )

    def test_slack_account_create_channel_with_public_flag_true(self):
        test_channel_name1 = 'test-channel-name-1'
        test_channel_id1 = 'Test Public Channel ID 1'
        test_response_json = {
            'group': {
                'id': test_channel_id1,
                'name': test_channel_name1,
            }
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/channels.create',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            test_method_response = test_bot.create_channel(
                channel_name=test_channel_name1,
                public=True,
            )

            self.assertEqual(
                test_response_json,
                test_method_response,
            )

    def test_slack_account_create_channel_with_public_flag_false(self):
        test_channel_name1 = 'test-channel-name-1'
        test_channel_id1 = 'Test Private Channel ID 1'
        test_response_json = {
            'group': {
                'id': test_channel_id1,
                'name': test_channel_name1,
            }
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/groups.create',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            test_method_response = test_bot.create_channel(
                channel_name=test_channel_name1,
                public=False,
            )

            self.assertEqual(
                test_response_json,
                test_method_response,
            )

    @patch(
        'virtual_ta.SlackAccount.user_ids',
        new_callable=PropertyMock
    )
    @patch(
        'virtual_ta.SlackAccount.public_channels_ids',
        new_callable=PropertyMock
    )
    def test_slack_account_invite_to_public_channel(
        self,
        mock_public_channels_ids,
        mock_user_ids,
    ):
        test_channel_name1 = 'test-channel-name-1'
        test_channel_name2 = 'test-channel-name-2'
        test_channel_id1 = 'Test Public Channel ID 1'
        test_channel_id2 = 'Test Public Channel ID 2'
        mock_public_channels_ids.return_value = {
            test_channel_name1: test_channel_id1,
            test_channel_name2: test_channel_id2,
        }

        test_user_name1 = 'test-user-name-1'
        test_user_name2 = 'test-user-name-2'
        test_user_id1 = 'test-user-id-1'
        test_user_id2 = 'test-user-id-2'
        mock_user_ids.return_value = {
            test_user_name1: test_user_id1,
            test_user_name2: test_user_id2,
        }

        test_expectations = test_response_json = {
            'group': {
                'id': test_channel_id1,
                'name': test_channel_name1,
                'latest': {
                    'user': test_user_name1,
                },
            },
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/channels.invite',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            test_method_response = test_bot.invite_to_public_channel(
                channel_name=test_channel_name1,
                user_name=test_user_name1,
            )

            self.assertEqual(
                test_expectations,
                test_method_response,
            )

    @patch(
        'virtual_ta.SlackAccount.user_ids',
        new_callable=PropertyMock
    )
    @patch(
        'virtual_ta.SlackAccount.private_channels_ids',
        new_callable=PropertyMock
    )
    def test_slack_account_invite_to_private_channel(
        self,
        mock_private_channels_ids,
        mock_user_ids,
    ):
        test_channel_name1 = 'test-channel-name-1'
        test_channel_name2 = 'test-channel-name-2'
        test_channel_id1 = 'Test Private Channel ID 1'
        test_channel_id2 = 'Test Private Channel ID 2'
        mock_private_channels_ids.return_value = {
            test_channel_name1: test_channel_id1,
            test_channel_name2: test_channel_id2,
        }

        test_user_name1 = 'test-user-name-1'
        test_user_name2 = 'test-user-name-2'
        test_user_id1 = 'test-user-id-1'
        test_user_id2 = 'test-user-id-2'
        mock_user_ids.return_value = {
            test_user_name1: test_user_id1,
            test_user_name2: test_user_id2,
        }

        test_expectations = test_response_json = {
            'group': {
                'id': test_channel_id1,
                'name': test_channel_name1,
                'latest': {
                    'user': test_user_name1,
                },
            },
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/groups.invite',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            test_method_response = test_bot.invite_to_private_channel(
                channel_name=test_channel_name1,
                user_name=test_user_name1,
            )

            self.assertEqual(
                test_expectations,
                test_method_response,
            )

    @patch(
        'virtual_ta.SlackAccount.public_channels_ids',
        new_callable=PropertyMock
    )
    def test_slack_account_set_public_channel_purpose(
        self,
        mock_public_channels_ids,
    ):
        test_channel_name1 = 'test-channel-name-1'
        test_channel_name2 = 'test-channel-name-2'
        test_channel_id1 = 'Test Public Channel ID 1'
        test_channel_id2 = 'Test Public Channel ID 2'
        mock_public_channels_ids.return_value = {
            test_channel_name1: test_channel_id1,
            test_channel_name2: test_channel_id2,
        }

        test_purpose = "Test Channel Purpose"
        test_expectations = test_response_json = {
            'purpose': test_purpose,
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/channels.setPurpose',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            test_method_response = test_bot.set_public_channel_purpose(
                channel_name=test_channel_name1,
                channel_purpose=test_purpose,
            )

            self.assertEqual(
                test_expectations,
                test_method_response,
            )

    @patch(
        'virtual_ta.SlackAccount.private_channels_ids',
        new_callable=PropertyMock
    )
    def test_slack_account_set_private_channel_purpose(
        self,
        mock_private_channels_ids,
    ):
        test_channel_name1 = 'test-channel-name-1'
        test_channel_name2 = 'test-channel-name-2'
        test_channel_id1 = 'Test Private Channel ID 1'
        test_channel_id2 = 'Test Private Channel ID 2'
        mock_private_channels_ids.return_value = {
            test_channel_name1: test_channel_id1,
            test_channel_name2: test_channel_id2,
        }

        test_purpose = "Test Channel Purpose"
        test_expectations = test_response_json = {
            'purpose': test_purpose,
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/groups.setPurpose',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            test_method_response = test_bot.set_private_channel_purpose(
                channel_name=test_channel_name1,
                channel_purpose=test_purpose,
            )

            self.assertEqual(
                test_expectations,
                test_method_response,
            )

    @patch(
        'virtual_ta.SlackAccount.public_channels_ids',
        new_callable=PropertyMock
    )
    def test_slack_account_set_public_channel_topic(
        self,
        mock_public_channels_ids,
    ):
        test_channel_name1 = 'test-channel-name-1'
        test_channel_name2 = 'test-channel-name-2'
        test_channel_id1 = 'Test Public Channel ID 1'
        test_channel_id2 = 'Test Public Channel ID 2'
        mock_public_channels_ids.return_value = {
            test_channel_name1: test_channel_id1,
            test_channel_name2: test_channel_id2,
        }

        test_topic = "Test Channel Topic"
        test_expectations = test_response_json = {
            'topic': test_topic,
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/channels.setTopic',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            test_method_response = test_bot.set_public_channel_topic(
                channel_name=test_channel_name1,
                channel_topic=test_topic,
            )

            self.assertEqual(
                test_expectations,
                test_method_response,
            )

    @patch(
        'virtual_ta.SlackAccount.private_channels_ids',
        new_callable=PropertyMock
    )
    def test_slack_account_set_private_channel_topic(
        self,
        mock_private_channels_ids,
    ):
        test_channel_name1 = 'test-channel-name-1'
        test_channel_name2 = 'test-channel-name-2'
        test_channel_id1 = 'Test Private Channel ID 1'
        test_channel_id2 = 'Test Private Channel ID 2'
        mock_private_channels_ids.return_value = {
            test_channel_name1: test_channel_id1,
            test_channel_name2: test_channel_id2,
        }

        test_topic = "Test Channel Topic"
        test_expectations = test_response_json = {
            'topic': test_topic,
        }

        test_token = 'Test Token Value'
        with requests_mock.Mocker() as mock_requests:
            mock_requests.register_uri(
                'POST',
                'https://slack.com/api/groups.setTopic',
                request_headers={
                    'Authorization': f'Bearer {test_token}',
                },
                status_code=200,
                json=test_response_json,
            )

            test_bot = SlackAccount(test_token)

            test_method_response = test_bot.set_private_channel_topic(
                channel_name=test_channel_name1,
                channel_topic=test_topic,
            )

            self.assertEqual(
                test_expectations,
                test_method_response,
            )

    @patch('virtual_ta.SlackAccount.create_channel')
    @patch('virtual_ta.SlackAccount.invite_to_private_channel')
    @patch('virtual_ta.SlackAccount.set_private_channel_purpose')
    @patch('virtual_ta.SlackAccount.set_private_channel_topic')
    @patch('virtual_ta.SlackAccount.get_private_channel_info')
    def test_slack_account_create_and_setup_private_channel(
        self,
        mock_get_private_channel_info,
        mock_set_private_channel_topic,
        mock_set_private_channel_purpose,
        mock_invite_to_private_channel,
        mock_create_channel,
    ):

        test_channel_name = 'test-channel-name'
        test_channel_id = 'Test Private Channel ID'
        mock_create_channel.return_value = {
            'group': {
                'id': test_channel_id,
                'name': test_channel_name,
            }
        }

        test_user_name1 = 'test-user-name-1'
        test_user_name2 = 'test-user-name-2'
        mock_invite_to_private_channel.side_effect = [
            {
                'group': {
                    'id': test_channel_id,
                    'name': test_channel_name,
                    'latest': {
                        'user': test_user_name1,
                    },
                },
            },
            {
                'group': {
                    'id': test_channel_id,
                    'name': test_channel_name,
                    'latest': {
                        'user': test_user_name2,
                    },
                },
            },
        ]

        test_purpose = "Test Channel Purpose"
        mock_set_private_channel_purpose.return_value = {
            'purpose': test_purpose,
        }

        test_topic = "Test Channel Topic"
        mock_set_private_channel_topic.return_value = {
            'topic': test_topic,
        }

        test_expectations = mock_get_private_channel_info.return_value = {
            'group': {
                'id': test_channel_id,
                'name': test_channel_name,
            }
        }

        test_token = 'Test Token Value'
        test_bot = SlackAccount(test_token)
        test_method_response = test_bot.create_and_setup_private_channel(
            channel_name=test_channel_name,
            users_to_invite=[test_user_name1, test_user_name2],
            channel_purpose=test_purpose,
            channel_topic=test_topic,
        )

        self.assertEqual(
            test_expectations,
            test_method_response,
        )

