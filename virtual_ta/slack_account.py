"""Creates a class for interfacing with the Slack Web API

This module encapsulates a Slack Account based upon an API token for a specific
Workspace, with methods for sending messages to users in the Workspace

See https://api.slack.com/web for more information about the Slack Web API

"""

import requests
from time import sleep
from typing import Dict, Generator, Iterable, List, Union


class SlackAccount(object):
    """Class for interfacing with the Slack Web API"""

    def __init__(self, api_token: str, user_name: str = '') -> None:
        """Initializes a SlackAccount object

        Args:
            api_token: a Slack API Token generated using either
                (1) https://api.slack.com/custom-integrations/legacy-tokens to
                    create a legacy token with full permissions scopes or
                (2) https://api.slack.com/apps to create an internal
                    integration app having at least the permission scopes of
                    channels:read, channels:write, chat:write:user,
                    groups:read, groups:write, im:history, im:read, and
                    users:read
            user_name: optional user name associated with Slack Account

        """

        self.api_token = api_token
        self.user_name = user_name

    def __repr__(self) -> str:
        """Returns string representation of Slack Account"""

        return (
            f'{self.__class__.__name__}(user_name={self.user_name})'
        )

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
    def public_channels(self) -> Generator[
        Dict[str, Union[Dict[str, str], List[str], str]],
        None,
        None
    ]:
        """Returns a generators of dicts, each describing a public channel

        Uses the Slack Web API call
        https://api.slack.com/methods/channels.list
        with no caching and with handling for paging; all parameters are set
        to values recommended in API documentation

        """

        cursor_position = ''
        while True:
            channels_response = requests.post(
                url='https://slack.com/api/channels.list',
                headers={
                    'Authorization': f'Bearer {self.api_token}',
                    'cursor': cursor_position,
                    'exclude_archived': 'true',
                    'exclude_members': 'true',
                    'limit': '200',
                },
            ).json()

            yield from channels_response['channels']

            try:
                cursor_position = (
                    channels_response['response_metadata']['next_cursor']
                )
            except KeyError:
                break

    @property
    def public_channels_ids(self) -> Dict[str, str]:
        """Returns a dict with public channel name -> channel id

        Uses the Slack Web API call with no caching

        """

        return {
            channel['name']: channel['id'] for channel in self.public_channels
        }

    @property
    def private_channels(self) -> Generator[
        Dict[str, Union[Dict[str, str], List[str], str]],
        None,
        None
    ]:
        """Returns a generators of dicts, each describing a private channel

        Uses the Slack Web API call
        https://api.slack.com/methods/groups.list
        with no caching; limited to private channels in the API Token's scope

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

        Uses the Slack Web API call with no caching; limited to private
        channels in the API Token's scope

        """

        return {
            channel['name']: channel['id'] for channel in self.private_channels
        }

    def get_public_channel_info(
        self,
        channel_name: str,
    ) -> Dict[
        str, Union[Dict[str, Union[Dict[str, str], List[str], str]], str]
    ]:
        """Returns dict of public channel information for the Slack Workspace

        Uses the Slack Web API call
        https://api.slack.com/methods/channels.info
        with no caching

        Args:
            channel_name: name of public channel in Slack Workspace

        Returns:
            A dictionary describing the public channel for the Slack Workspace

        """

        return requests.post(
            url='https://slack.com/api/channels.info',
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Content-type': 'application/x-www-form-urlencoded',
            },
            data={
                'channel': self.public_channels_ids[channel_name.lower()],
                'include_locale': 'true',
            }
        ).json()

    def get_private_channel_info(
        self,
        channel_name: str,
    ) -> Dict[
        str, Union[Dict[str, Union[Dict[str, str], List[str], str]], str]
    ]:
        """Returns dict of private channel information for the Slack Workspace

        Uses the Slack Web API call
        https://api.slack.com/methods/groups.info
        with no caching; limited to private channels in the API Token's scope

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

    def create_channel(
        self,
        channel_name: str,
        public=True,
    ) -> Dict[str, Union[Dict[str, Union[List[str], str]], str]]:
        """Creates a channel in the Slack Workspace

        Uses the Slack Web API with no caching; the user associated with API
        Token is automatically added to the created channel

        Args:
            channel_name: name of channel to create
            public: determines whether channel is public; defaults to True; if
                set to False, then channel will be private

        Returns:
            A dictionary describing the channel creation results

        """

        if public:
            return requests.post(
                url='https://slack.com/api/channels.create',
                headers={
                    'Authorization': f'Bearer {self.api_token}',
                    'Content-type': 'application/json; charset=utf-8',
                },
                json={
                    'name': channel_name,
                }
            ).json()
        else:
            return requests.post(
                url='https://slack.com/api/groups.create',
                headers={
                    'Authorization': f'Bearer {self.api_token}',
                    'Content-type': 'application/json; charset=utf-8',
                },
                json={
                    'name': channel_name,
                }
            ).json()

    def invite_to_public_channel(
        self,
        channel_name: str,
        user_name: str,
    ) -> Dict[
        str, Union[Dict[str, Union[Dict[str, str], List[str], str]], str]
    ]:
        """Invites user to join public channel in the Slack Workspace

        Uses the Slack Web API call
        https://api.slack.com/methods/channels.invite
        with no caching

        Args:
            channel_name: name of public channel in Slack Workspace
            user_name: user name of user to invite to public channel

        Returns:
            A dictionary describing the channel-invitation results

        """

        return requests.post(
            url='https://slack.com/api/channels.invite',
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Content-type': 'application/json; charset=utf-8',
            },
            json={
                'channel': self.public_channels_ids[channel_name.lower()],
                'user': self.user_ids[user_name],
            }
        ).json()

    def invite_to_private_channel(
        self,
        channel_name: str,
        user_name: str,
    ) -> Dict[
        str, Union[Dict[str, Union[Dict[str, str], List[str], str]], str]
    ]:
        """Invites user to join private channel in the Slack Workspace

        Uses the Slack Web API call
        https://api.slack.com/methods/groups.invite
        with no caching; limited to private channels in the API Token's scope

        Args:
            channel_name: name of private channel in Slack Workspace
            user_name: user name of user to invite to private channel

        Returns:
            A dictionary describing the channel-invitation results

        """

        return requests.post(
            url='https://slack.com/api/groups.invite',
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Content-type': 'application/json; charset=utf-8',
            },
            json={
                'channel': self.private_channels_ids[channel_name.lower()],
                'user': self.user_ids[user_name],
            }
        ).json()

    def set_public_channel_purpose(
        self,
        channel_name: str,
        channel_purpose: str,
    ) -> Dict[str, str]:
        """Sets purpose for public channel in the Slack Workspace

        Uses the Slack Web API call
        https://api.slack.com/methods/channels.setPurpose
        with no caching

        Args:
            channel_name: name of public channel in Slack Workspace
            channel_purpose: purpose to set for public channel

        Returns:
            A dictionary describing the results of setting the channel purpose

        """

        return requests.post(
            url='https://slack.com/api/channels.setPurpose',
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Content-type': 'application/json; charset=utf-8',
            },
            json={
                'channel': self.public_channels_ids[channel_name.lower()],
                'purpose': channel_purpose,
            }
        ).json()

    def set_private_channel_purpose(
        self,
        channel_name: str,
        channel_purpose: str,
    ) -> Dict[str, str]:
        """Sets purpose for private channel in the Slack Workspace

        Uses the Slack Web API call
        https://api.slack.com/methods/groups.setPurpose
        with no caching; limited to private channels in the API Token's scope

        Args:
            channel_name: name of private channel in Slack Workspace
            channel_purpose: purpose to set for private channel

        Returns:
            A dictionary describing the results of setting the channel purpose

        """

        return requests.post(
            url='https://slack.com/api/groups.setPurpose',
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Content-type': 'application/json; charset=utf-8',
            },
            json={
                'channel': self.private_channels_ids[channel_name.lower()],
                'purpose': channel_purpose,
            }
        ).json()

    def set_public_channel_topic(
        self,
        channel_name: str,
        channel_topic: str,
    ) -> Dict[str, str]:
        """Sets purpose for public channel in the Slack Workspace

        Uses the Slack Web API call
        https://api.slack.com/methods/channels.setTopic
        with no caching

        Args:
            channel_name: name of public channel in Slack Workspace
            channel_topic: topic to set for public channel

        Returns:
            A dictionary describing the results of setting the channel topic

        """

        return requests.post(
            url='https://slack.com/api/channels.setTopic',
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Content-type': 'application/json; charset=utf-8',
            },
            json={
                'channel': self.public_channels_ids[channel_name.lower()],
                'topic': channel_topic,
            }
        ).json()

    def set_private_channel_topic(
        self,
        channel_name: str,
        channel_topic: str,
    ) -> Dict[str, str]:
        """Sets purpose for private channel in the Slack Workspace

        Uses the Slack Web API call
        https://api.slack.com/methods/groups.setTopic
        with no caching; limited to private channels in the API Token's scope

        Args:
            channel_name: name of private channel in Slack Workspace
            channel_topic: topic to set for private channel

        Returns:
            A dictionary describing the results of setting the channel topic

        """

        return requests.post(
            url='https://slack.com/api/groups.setTopic',
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Content-type': 'application/json; charset=utf-8',
            },
            json={
                'channel': self.private_channels_ids[channel_name.lower()],
                'topic': channel_topic,
            }
        ).json()

    def create_and_setup_channel(
        self,
        channel_name: str,
        user_names_to_invite: Iterable[str],
        channel_purpose: str,
        channel_topic: str,
        public: bool = True,
        sleep_time: int = 1,
    ) -> Dict[str, Union[Dict[str, Union[List[str], str]], str]]:
        """Creates and sets up a channel in the Slack Workspace

        Uses the Slack Web API call with no caching and naive handling of rate
        limit by sleeping after each channel-setup operation; see
        https://api.slack.com/docs/rate-limits

        Args:
            channel_name: name of channel to create
            user_names_to_invite: iterable of user names to invite to channel
            channel_purpose: purpose to set for channel
            channel_topic: topic to set for channel
            public: determines whether channel is public; defaults to True; if
                set to False, then channel will be private
            sleep_time: determines the number of seconds to sleep after each
                channel-creation/setup operation; defaults to one (1)

        Returns:
            A dictionary describing the channel creation results

        """

        if public:
            self.create_channel(
                channel_name=channel_name,
                public=True,
            )
            sleep(sleep_time)
            for user_name in user_names_to_invite:
                self.invite_to_public_channel(
                    channel_name=channel_name,
                    user_name=user_name,
                )
                sleep(sleep_time)
            self.set_public_channel_purpose(
                channel_name=channel_name,
                channel_purpose=channel_purpose,
            )
            sleep(sleep_time)
            self.set_public_channel_topic(
                channel_name=channel_name,
                channel_topic=channel_topic,
            )
            return_value = self.get_public_channel_info(channel_name)

        else:
            self.create_channel(
                channel_name=channel_name,
                public=False,
            )
            sleep(sleep_time)
            for user_name in user_names_to_invite:
                self.invite_to_private_channel(
                    channel_name=channel_name,
                    user_name=user_name,
                )
                sleep(sleep_time)
            self.set_private_channel_purpose(
                channel_name=channel_name,
                channel_purpose=channel_purpose,
            )
            sleep(sleep_time)
            self.set_private_channel_topic(
                channel_name=channel_name,
                channel_topic=channel_topic,
            )
            sleep(sleep_time)
            return_value = self.get_private_channel_info(channel_name)

        return return_value
