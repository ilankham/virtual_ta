from datetime import datetime, timedelta
import json
from time import sleep

import requests


class BlackboardClass(object):
    def __init__(
        self,
        server_address,
        course_id,
        application_key,
        application_secret
    ):
        self.server_address = server_address
        self.course_id = course_id
        self.application_key = application_key
        self.application_secret = application_secret

        self.__api_token = None
        self.api_token_expiration_datetime = None

    @property
    def api_token(self):
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
                verify=False
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

    def create_gradebook_column(
        self,
        name,
        due_date,
        *,
        external_id='',
        description='',
        max_score_possible=0,
        available_to_students='Yes',
        grading_type='Manual',
    ):
        api_request_url = (
            'https://' +
            self.server_address +
            f'/learn/api/public/v2/courses/courseId:{self.course_id}'
            f'/gradebook/columns'
        )

        request_data = {
                    "name": name,
                    "description": description,
                    "score": {
                        "possible": max_score_possible,
                    },
                    "availability": {
                        "available": available_to_students
                    },
                    "grading": {
                        "type": grading_type,
                        "due": due_date,
                    },
            }
        if external_id:
            request_data["externalId"] = external_id

        return_value = requests.post(
            api_request_url,
            data=json.dumps(request_data),
            headers={
                'Authorization': 'Bearer ' + self.api_token,
                'Content-Type': 'application/json'
            },
            verify=False,
        ).json()
        return return_value

    @property
    def gradebook_columns(self):
        api_request_url = (
            'https://' +
            self.server_address +
            f'/learn/api/public/v2/courses/courseId:{self.course_id}'
            '/gradebook/columns'
        )

        while api_request_url:
            api_response = requests.get(
                api_request_url,
                headers={'Authorization': 'Bearer ' + self.api_token},
                verify=False
            ).json()
            yield from api_response['results']
            try:
                api_request_url = api_response['paging']['nextPage']
            except KeyError:
                api_request_url = None

    @property
    def gradebook_columns_primary_ids(self):
        return {
            column['name']: column['id'] for column in self.gradebook_columns
        }

    def set_grade(
        self,
        column_primary_id,
        user_name,
        grade_as_score,
        *,
        grade_as_text='',
        grade_feedback='',
    ):
        api_request_url = (
            'https://' +
            self.server_address +
            f'/learn/api/public/v2/courses/courseId:{self.course_id}'
            f'/gradebook/columns/{column_primary_id}'
            f'/users/userName:{user_name}'
        )
        return_value = requests.patch(
            api_request_url,
            data=json.dumps({
                'score': grade_as_score,
                'text': grade_as_text,
                'feedback': grade_feedback,
            }),
            headers={
                'Authorization': 'Bearer ' + self.api_token,
                'Content-Type': 'application/json'
            },
            verify=False,
        ).json()
        return return_value

    def update_gradebook_column(
        self,
        column_primary_id,
        grades_as_scores,
        grades_as_text=None,
        grades_feedback=None,
    ):
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
                )
            )

        return return_value

    def get_grades(self, column_primary_id):
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
                verify=False
            ).json()
            yield from api_response['results']
            try:
                api_request_url = api_response['paging']['nextPage']
            except KeyError:
                api_request_url = None

    def get_grades_by_primary_user_id(self, column_primary_id):
        return_value = {
            grade['userId']: {
                'score': grade.get('score', ''),
                'text': grade.get('text', ''),
                'feedback': grade.get('feedback', ''),
            } for grade in self.get_grades(column_primary_id)
        }
        return return_value

    def get_primary_user_id(self, user_name):
        api_request_url = (
            'https://' +
            self.server_address +
            f'/learn/api/public/v1/courses/courseId:{self.course_id}'
            f'/users/userName:{user_name}'
        )
        return_value = requests.get(
            api_request_url,
            headers={'Authorization': 'Bearer ' + self.api_token},
            verify=False
        ).json()
        return return_value.get('userId', '')

    def get_grade(self, column_primary_id, user_name):
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
            verify=False,
        ).json()
        return return_value
