import requests


class SlackBot(object):
    def __init__(self, api_token=None):
        self.api_token = api_token

    def set_api_token_from_file(self, fp):
        self.api_token = fp.readline()

    @property
    def user_ids(self):
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
    def user_dm_channels(self):
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

    def direct_message_by_username(self, messages_by_username):
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
