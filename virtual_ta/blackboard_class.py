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
