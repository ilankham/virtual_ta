class SlackBot(object):
    def __init__(self, api_token=None):
        self.api_token = api_token

    def set_api_token_from_file(self, fp):
        self.api_token = fp.readline()
