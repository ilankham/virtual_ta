"""Creates a class for interfacing with Slack Web API

This module creates a class for encapsulating a Slack Account based upon API
token, including a method for reading an API token from a file and for making
Slack Web API calls to send messages to users in the corresponding Slack
Workspace by username.

See https://api.slack.com/web for more information about the Slack Web API.

"""

from io import StringIO, TextIOWrapper
from typing import Union

import requests

FileIO = Union[StringIO, TextIOWrapper]


class SlackAccount(object):
    """Class for interfacing with Slack Web API"""

    def __init__(self, api_token: str = None) -> None:
        """Initializes SlackAccount object using API Token

        Args:
            api_token: a Slack API Token generated using either
                (1) https://api.slack.com/custom-integrations/legacy-tokens to
                    create a legacy token with full permissions scopes or
                (2) https://api.slack.com/apps to create an internal
                    integration app having at least the permission scopes of
                    chat:write:user, im:read, and users:read

        """
        self.api_token = api_token

    def set_api_token_from_file(self, fp: FileIO) -> None:
        """Loads Slack API Token from file

        Args:
            fp: pointer to file or file-like object that is ready to read from
                and contains a Slack API Token generated using either
                (1) https://api.slack.com/custom-integrations/legacy-tokens to
                    create a legacy token with full permissions scopes or
                (2) https://api.slack.com/apps to create an internal
                    integration app having at least the permission scopes of
                    chat:write:user, im:read, and users:read

        """
        self.api_token = fp.readline()

    @property
    def user_ids(self) -> dict:
        """Returns dictionary with username -> user id

        Uses a Slack Web API call https://api.slack.com/methods/users.list
        with no caching

        """
        users_list_response = requests.post(
            url="https://slack.com/api/users.list",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-type": "application/json",
            },
        )
        return_value = {}
        for user in users_list_response.json()['members']:
            return_value[user['name']] = user['id']

        return return_value

    @property
    def user_dm_channels(self) -> dict:
        """Returns dictionary with username -> user direct message channel id

        Uses a Slack Web API call https://api.slack.com/methods/im.list
        with no caching

        """
        im_list_response = requests.post(
            url="https://slack.com/api/im.list",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-type": "application/json",
            },
        )
        channels = {}
        for channel in im_list_response.json()['ims']:
            channels[channel['user']] = channel['id']

        return_value = {}
        users = self.user_ids
        for user in users:
            return_value[user] = channels.get(users[user], None)

        return return_value

    def direct_message_by_username(self, messages_by_username: dict) -> dict:
        """Sends direct messages using Slack Web API calls.

        Uses Slack Web API call https://api.slack.com/methods/chat.postMessage

        Args:
            messages_by_username: dictionary keyed by username with values the
                messages to send to each user

        Returns:
            dictionary keyed by direct message channel id with values the
                messages sent to the corresponding users

        """
        user_dm_channels = self.user_dm_channels

        return_value = {}
        for username in messages_by_username:
            requests.post(
                url="https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-type": "application/json",
                },
                json={
                    "channel": user_dm_channels[username],
                    "text": messages_by_username[username],
                    "as_user": "true"
                }
            )
            return_value[user_dm_channels[username]] = (
                messages_by_username[username]
            )

        return return_value
