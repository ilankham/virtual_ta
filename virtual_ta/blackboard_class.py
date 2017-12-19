from datetime import datetime, timedelta
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
