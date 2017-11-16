import requests


class SlackBot(object):
    def __init__(self, api_token=None):
        self.api_token = api_token

    def set_api_token_from_file(self, fp):
        self.api_token = fp.readline()

    def direct_message_by_username(self, messages_by_username):
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

        users_list_response = requests.post(
            url="https://slack.com/api/users.list",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-type": "application/json",
            },
        )
        users = {}
        for user in users_list_response.json()['members']:
            users[user['name']] = user['id']

        user_dm_channels = {}
        for user in users:
            user_dm_channels[user] = channels.get(users[user], None)

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
