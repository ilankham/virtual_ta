"""Creates a class for interfacing with the Blackboard Learn REST API

This module encapsulates a Blackboard Course based upon a courseId from a
specific Blackboard Learn instance server address, along with an application
key and application secret for an API REST integration registered at the
Blackboard API Dev Portal (https://developer.blackboard.com/), and also
registered with the Blackboard Learn instance and associated with a user
account having sufficient access privileges to edit courseId's gradebook

See https://developer.blackboard.com/portal/displayApi for more information
about the Blackboard Learn REST API

"""

from datetime import datetime, timedelta
from functools import wraps
import json
from time import sleep
from typing import Callable, Dict, Generator, List, Union

import requests


class BlackboardCourse(object):
    """Class for interfacing with the Blackboard Learn REST API"""

    def __init__(
        self,
        course_id: str,
        server_address: str,
        application_key: str,
        application_secret: str,
        verify_ssl_certificate: bool = True,
    ) -> None:
        """Initializes a BlackboardCourse object

        Args:
            course_id: a courseId (not primary id) associated with the
                Blackboard Learn instance at server_address
            server_address: the server address for a Blackboard Learn instance,
                including port number, if needed; 'https://' is automatically
                prepended, if not present
            application_key: application key for an API REST integration
                registered at the Blackboard API Dev Portal
                (https://developer.blackboard.com/), and also registered with
                the Blackboard Learn instance at server_address and associated
                with a user account having sufficient access privileges to edit
                course_id's gradebook
            application_secret: application secret corresponding to
                application_key
            verify_ssl_certificate: determines whether an ssl certificate is
                verified during HTTPS requests; defaults to True

        """

        self.course_id = course_id
        if server_address.startswith('https://'):
            server_address = server_address[8:]
        self.server_address = server_address
        self.application_key = application_key
        self.application_secret = application_secret
        self.verify_ssl_certificate = verify_ssl_certificate

        self.__api_token: str = None
        self.api_token_expiration_datetime: datetime = None

    def __repr__(self) -> str:
        """Returns string representation of Blackboard Course"""

        return (
            f'{self.__class__.__name__}(course_id={self.course_id}, '
            f'server_address={self.server_address})'
        )

    @property
    def api_token(self) -> str:
        """Returns a Blackboard Learn REST API Token for the associated Course

        Uses the Blackboard Learn REST API call
        f'http://{self.server_address}/learn/api/public/v1/oauth2/token'
        with the API token value cached unless expired

        """

        if self.__api_token is None:
            api_request_url = (
                'https://' +
                self.server_address +
                '/learn/api/public/v1/oauth2/token'
            )
            api_token_response = requests.post(
                api_request_url,
                data={
                    'grant_type': 'client_credentials'
                },
                auth=(self.application_key, self.application_secret),
                verify=self.verify_ssl_certificate,
            ).json()
            self.__api_token = api_token_response['access_token']
            self.api_token_expiration_datetime = (
                datetime.now() +
                timedelta(seconds=api_token_response['expires_in'])
            )

        time_until_api_token_expiration = (
            self.api_token_expiration_datetime - datetime.now()
        ).total_seconds()
        if time_until_api_token_expiration <= 1:
            self.__api_token = None
            sleep(1)
            self.__api_token = self.api_token

        return self.__api_token

    @staticmethod
    def handle_api_paging(wrapped_fcn: Callable) -> Callable:
        """Decorator for handling Blackboard Learn REST API paging

        Args:
            wrapped_fcn: function having one fixed argument (api_request_url),
                passing additional **kwargs arguments to requests.get, and
                returning a response object with optional paging information

        Returns:
            A callable version of wrapped_fcn handling paging

        """

        @wraps(wrapped_fcn)
        def yield_json_results_helper(api_request_url='', **kwargs):

            while api_request_url:
                api_response = wrapped_fcn(api_request_url, **kwargs)
                yield from api_response.json().get('results', [])
                try:
                    api_request_url = api_response.json()['paging']['nextPage']
                except KeyError:
                    api_request_url = None

        return yield_json_results_helper

    @property
    def gradebook_columns(self) -> Generator[dict, None, None]:
        """Returns a generator of dicts, each describing a gradebook column

        Uses the Blackboard Learn REST API call
        f'http://{self.server_address}/learn/api/public/v2/courses'
        f'/courseId:{self.course_id}/gradebook/columns'
        with no caching

        """

        url = (
            'https://' +
            self.server_address +
            f'/learn/api/public/v2/courses/courseId:{self.course_id}'
            '/gradebook/columns'
        )

        request_get_options = {
            'headers': {
                'Authorization': 'Bearer ' + self.api_token,
            },
            'verify': self.verify_ssl_certificate,
        }

        @self.handle_api_paging
        def __get_gradebook_columns_response(
            api_request_url: str ='',
            **kwargs,
        ) -> requests.Response:
            return requests.get(
                api_request_url,
                **kwargs,
            )

        return __get_gradebook_columns_response(url, **request_get_options)

    @property
    def gradebook_columns_primary_ids(self) -> Dict[str, str]:
        """Returns a dict with gradebook column name -> column primary id

        Uses the Blackboard Learn REST API with no caching

        """

        return {
            column['name']: column['id'] for column in self.gradebook_columns
        }

    @property
    def gradebook_schemas(self) -> Generator[Dict[str, str], None, None]:
        """Returns a generator of dicts, each describing a gradebook schema

        Uses the Blackboard Learn REST API call
        f'http://{self.server_address}/learn/api/public/v1/courses'
        f'/courseId:{self.course_id}/gradebook/schemas'
        with no caching

        """

        api_request_url = (
            'https://' +
            self.server_address +
            f'/learn/api/public/v1/courses/courseId:{self.course_id}'
            '/gradebook/schemas'
        )

        while api_request_url:
            api_response = requests.get(
                api_request_url,
                headers={'Authorization': 'Bearer ' + self.api_token},
                verify=self.verify_ssl_certificate,
            ).json()
            yield from api_response['results']
            try:
                api_request_url = api_response['paging']['nextPage']
            except KeyError:
                api_request_url = None

    @property
    def gradebook_schemas_primary_ids(self) -> Dict[str, str]:
        """Returns a dict with gradebook schema name -> schema primary id

        Uses the Blackboard Learn REST API with no caching

        """

        return {
            schema['scaleType']: schema['id']
            for schema in self.gradebook_schemas
        }

    def create_gradebook_column(
        self,
        name: str,
        due_date: str,
        *,
        description: str ='',
        max_score_possible: int =0,
        available_to_students: str ='Yes',
        grading_type: str ='Manual',
        scale_type: str ='Text',
    ) -> Dict[str, str]:
        """Creates gradebook column with specified properties

        Uses the Blackboard Learn REST API call
        f'http://{self.server_address}/learn/api/public/v2/courses
        f'/courseId:{self.course_id}/gradebook/columns'
        with no caching

        Args:
            name: display name of column to create
            due_date: due date for column in ISO 8601 format; e.g., for
                datetime.datetime.strftime(), the format could be written as
                '%Y-%m-%dT%H:%M:%SZ'
            description: display description of column to create
            max_score_possible: display value for maximum score possible for
                assignments corresponding to column; defaulting to 0, which
                suppresses display of maximum grade in student's gradebook view
            available_to_students: if 'Yes', then the column is displayed
                student's gradebook view; if 'No', then the column is not
                displayed student's gradebook view; defaults to 'Yes'
            grading_type: allowable values are 'Attempts', 'Calculated', and
                'Manual'; defaults to 'Manual'
            scale_type: allowable values are 'Score', 'Text', 'Percentage',
                and 'CompleteIncomplete'; defaults to 'Text'

        Returns:
            A dictionary describing the resulting gradebook column

        """

        api_request_url = (
            'https://' +
            self.server_address +
            f'/learn/api/public/v2/courses/courseId:{self.course_id}'
            f'/gradebook/columns'
        )

        # handle exception if server version doesn't support gradebook schemas:
        try:
            schema_id = self.gradebook_schemas_primary_ids[scale_type]
        except KeyError:
            schema_id = None

        request_data = {
            'name': name,
            'description': description,
            'score': {
                'possible': max_score_possible,
            },
            'availability': {
                'available': available_to_students
            },
            'grading': {
                'type': grading_type,
                'due': due_date,
                'schemaId': schema_id,
            },
        }

        return_value = requests.post(
            api_request_url,
            data=json.dumps(request_data),
            headers={
                'Authorization': 'Bearer ' + self.api_token,
                'Content-Type': 'application/json'
            },
            verify=self.verify_ssl_certificate,
        ).json()
        return return_value

    def get_user_primary_id(self, user_name: str) -> str:
        """Returns primary id associated with user_name

        Uses the Blackboard Learn REST API call
        f'http://{self.server_address}/learn/api/public/v1/courses
        f'/courseId:{self.course_id}/users/userName:{user_name}'
        with no caching

        Args:
            user_name: name of a user associated with the course

        Returns:
            A string containing the primary user id associated with user_name,
            defaulting to an empty string if no primary user id is found

        """

        api_request_url = (
            'https://' +
            self.server_address +
            f'/learn/api/public/v1/courses/courseId:{self.course_id}'
            f'/users/userName:{user_name}'
        )
        return_value = requests.get(
            api_request_url,
            headers={'Authorization': 'Bearer ' + self.api_token},
            verify=self.verify_ssl_certificate
        ).json()
        return return_value.get('userId', '')

    def get_grade(
        self,
        column_primary_id: str,
        user_name: str
    ) -> Dict[str, str]:
        """Returns dict describing grade for user_name from a gradebook column

        Uses the Blackboard Learn REST API call
        f'http://{self.server_address}/learn/api/public/v2/courses
        f'/courseId:{self.course_id}/gradebook/columns/{column_primary_id}'
        f'/users/userName:{user_name}'
        with no caching

        Args:
            column_primary_id: primary id for a gradebook column associated
                with the course
            user_name: name of a user associated with course

        Returns:
            A dictionary describing the grade of user_name from the course's
            gradebook column associated with column_primary_id

        """

        api_request_url = (
            'https://' +
            self.server_address +
            f'/learn/api/public/v2/courses/courseId:{self.course_id}'
            f'/gradebook/columns/{column_primary_id}'
            f'/users/userName:{user_name}'
        )
        return_value = requests.get(
            api_request_url,
            headers={
                'Authorization': 'Bearer ' + self.api_token,
                'Content-Type': 'application/json'
            },
            verify=self.verify_ssl_certificate,
        ).json()
        return return_value

    def get_grades_in_column(
        self,
        column_primary_id: str
    ) -> Generator[Dict[str, str], None, None]:
        """Returns generator yielding grade information for a gradebook column

        Uses the Blackboard Learn REST API call
        f'http://{self.server_address}/learn/api/public/v2/courses
        f'/courseId:{self.course_id}/gradebook/columns/{column_primary_id}'
        f'/users'
        with no caching and with handling for paging

        Args:
            column_primary_id: primary id for a gradebook column associated
                with the course

        Returns:
            A generator yielding grade information from the course's gradebook
            column associated with column_primary_id

        """

        api_request_url = (
            'https://' +
            self.server_address +
            f'/learn/api/public/v2/courses/courseId:{self.course_id}'
            f'/gradebook/columns/{column_primary_id}/users'
        )

        while api_request_url:
            api_response = requests.get(
                api_request_url,
                headers={'Authorization': 'Bearer ' + self.api_token},
                verify=self.verify_ssl_certificate
            ).json()
            yield from api_response['results']
            try:
                api_request_url = api_response['paging']['nextPage']
            except KeyError:
                api_request_url = None

    def set_grade(
        self,
        column_primary_id: str,
        user_name: str,
        grade_as_score: Union[int, str],
        *,
        grade_as_text: str = '',
        grade_feedback: str = '',
        overwrite: bool = True,
    ) -> Dict[str, str]:
        """Sets grade for user_name in gradebook column as score/text/feedback

        Uses the Blackboard Learn REST API call
        f'http://{self.server_address}/learn/api/public/v2/courses
        f'/courseId:{self.course_id}/gradebook/columns/{column_primary_id}'
        f'/users/userName:{user_name}'
        with no caching

        Args:
            column_primary_id: primary id for a gradebook column associated
                with the course
            user_name: name of a user associated with course
            grade_as_score: numerical value, or a string convertible to a
                numerical value, to set for user_name's grade in the gradebook
                column with column_primary_id
            grade_as_text: corresponding textual value to set for grade; note
                that these values are only retained by the Blackboard server
                if the column's Primary Display type has been set to 'Text';
                defaults to the empty string, which suppresses text display
            grade_feedback: corresponding feedback to set for grade; defaults
                to the empty string, which suppresses grade feedback
            overwrite: determines whether a pre-existing grade value is
                overwritten; defaults to True

        Returns:
            A dictionary describing the grade of user_name from the course's
            gradebook column associated with column_primary_id

        """

        api_request_url = (
            'https://' +
            self.server_address +
            f'/learn/api/public/v2/courses/courseId:{self.course_id}'
            f'/gradebook/columns/{column_primary_id}'
            f'/users/userName:{user_name}'
        )
        current_grade = {}
        if not overwrite:
            current_grade = self.get_grade(column_primary_id, user_name)
        if overwrite or current_grade.get('score', None) is None:
            return_value = requests.patch(
                api_request_url,
                data=json.dumps({
                    'score': str(grade_as_score),
                    'text': grade_as_text,
                    'feedback': grade_feedback,
                }),
                headers={
                    'Authorization': 'Bearer ' + self.api_token,
                    'Content-Type': 'application/json'
                },
                verify=self.verify_ssl_certificate,
            ).json()
        else:
            return_value = current_grade
        return return_value

    def set_grades_in_column(
        self,
        column_primary_id: str,
        grades_as_scores: dict,
        grades_as_text: dict = None,
        grades_feedback: dict = None,
        overwrite: bool = True,
    ) -> List[Dict[str, str]]:
        """Sets grades in gradebook column as score/text/feedback

        Uses the Blackboard Learn REST API call with no caching

        Args:
            column_primary_id: primary id for a gradebook column associated
                with the course
            grades_as_scores: dictionary keyed by user names with numerical
                values, or strings convertible to numerical values, to set for
                each corresponding user's grade in the gradebook column with
                column_primary_id
            grades_as_text: dictionary keyed by user names with corresponding
                textual values to set for users' grades; note that these values
                are only retained by the Blackboard server if the column's
                Primary Display type has been set to 'Text'
            grades_feedback: dictionary keyed by user names with corresponding
                feedback values to set for users' grades
            overwrite: determines whether pre-existing grade values are
                overwritten

        Returns:
            A list of dictionaries describing grades from the course's
            gradebook column associated with column_primary_id for users whose
            user names are in grades_as_scores.keys()

        """

        if grades_as_text is None:
            grades_as_text = {}
        if grades_feedback is None:
            grades_feedback = {}

        return_value = []
        for username, score in grades_as_scores.items():
            return_value.append(
                self.set_grade(
                    column_primary_id=column_primary_id,
                    user_name=username,
                    grade_as_score=score,
                    grade_as_text=grades_as_text.get(username, ''),
                    grade_feedback=grades_feedback.get(username, ''),
                    overwrite=overwrite,
                )
            )

        return return_value
