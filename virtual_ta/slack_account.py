"""Creates a class for interfacing with the Slack Web API

This module encapsulates a Slack Account based upon an API token for a specific
Workspace, with methods for sending messages to users in the Workspace

See https://api.slack.com/web for more information about the Slack Web API

"""

import requests
from typing import Dict, Generator, List, Union


class SlackAccount(object):
    """Class for interfacing with the Slack Web API"""

    def __init__(self, api_token: str) -> None:
        """Initializes a SlackAccount object

        Args:
            api_token: a Slack API Token generated using either
                (1) https://api.slack.com/custom-integrations/legacy-tokens to
                    create a legacy token with full permissions scopes or
                (2) https://api.slack.com/apps to create an internal
                    integration app having at least the permission scopes of
                    chat:write:user, groups:read, groups:write, im:history,
                    im:read, and users:read

        """

        self.api_token = api_token

    @property
    def user_ids(self) -> Dict[str, str]:
        """Returns a dict with username -> user id

        Uses the Slack Web API call https://api.slack.com/methods/users.list
        with no caching

        """

        users_list_response = requests.post(
            url='https://slack.com/api/users.list',
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Content-type': 'application/json',
            },
        )
        return_value = {}
        for user in users_list_response.json()['members']:
            return_value[user['name']] = user['id']

        return return_value

    @property
    def user_dm_channels(self) -> Dict[str, str]:
        """Returns a dict with username -> user direct message channel id

        Uses the Slack Web API call https://api.slack.com/methods/im.list
        with no caching

        """

        im_list_response = requests.post(
            url='https://slack.com/api/im.list',
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Content-type': 'application/json',
            },
        )
        channels = {}
        for channel in im_list_response.json()['ims']:
            channels[channel['user']] = channel['id']

        return_value = {}
        users = self.user_ids
        for user in users:
            return_value[user] = channels.get(users[user], '')

        return return_value

    def direct_message_by_username(
        self,
        messages_by_username: dict
    ) -> Dict[str, str]:
        """Sends direct messages to users by username

        Uses the Slack Web API call
        https://api.slack.com/methods/chat.postMessage

        Args:
            messages_by_username: dictionary keyed by username with values the
                messages to send to each user

        Returns:
            A dictionary keyed by direct message channel id and as values the
            messages sent to the corresponding users

        """

        user_dm_channels = self.user_dm_channels

        return_value = {}
        for username in messages_by_username:
            requests.post(
                url='https://slack.com/api/chat.postMessage',
                headers={
                    'Authorization': f'Bearer {self.api_token}',
                    'Content-type': 'application/json',
                },
                json={
                    'channel': user_dm_channels[username],
                    'text': messages_by_username[username],
                    'as_user': 'true'
                }
            )
            return_value[user_dm_channels[username]] = (
                messages_by_username[username]
            )

        return return_value

    def get_most_recent_direct_messages(
        self,
        username: str,
        message_count: Union[int, str] = 1,
    ) -> Generator[str, None, None]:
        """Gets most recent direct messages sent to username

        Uses the Slack Web API call
        https://api.slack.com/methods/im.history
        with no caching or paging support

        Args:
            username: username of user in Slack Workspace
            message_count: the number of most recent DMs to retrieve

        Returns:
            A generator of messages in reverse chronological order

        """

        most_recent_dms_response = requests.post(
            url='https://slack.com/api/im.history',
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Content-type': 'application/x-www-form-urlencoded',
            },
            data={
                'channel': self.user_dm_channels[username],
                'count': str(message_count),
            }
        ).json()

        return_value = (
            message['text'] for message in most_recent_dms_response['messages']
        )

        return return_value

    @property
    def private_channels(self) -> Generator[
        Dict[str, Union[Dict[str, str], List[str], str]],
        None,
        None
    ]:
        """Returns a generators of dicts, each describing a private channel

        Uses the Slack Web API call
        https://api.slack.com/methods/groups.list
        with no caching

        """

        return_value = requests.post(
            url='https://slack.com/api/groups.list',
            headers={
                'Authorization': f'Bearer {self.api_token}',
            },
        ).json()

        yield from return_value['groups']

    @property
    def private_channels_ids(self) -> Dict[str, str]:
        """Returns a dict with private channel name -> channel id

        Uses the Slack Web API call with no caching

        """

        return {
            channel['name']: channel['id'] for channel in self.private_channels
        }

    def get_private_channel_info(
        self,
        channel_name: str,
    ) -> Dict[
        str, Union[Dict[str, Union[Dict[str, str], List[str], str]], str]
    ]:
        """Returns dict of private channel information for the Slack Workspace

        Uses the Slack Web API call
        https://api.slack.com/methods/groups.info
        with no caching

        Args:
            channel_name: name of private channel in Slack Workspace

        Returns:
            A dictionary describing the private channel for the Slack Workspace

        """

        return requests.post(
            url='https://slack.com/api/groups.info',
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Content-type': 'application/x-www-form-urlencoded',
            },
            data={
                'channel': self.private_channels_ids[channel_name.lower()],
            }
        ).json()
