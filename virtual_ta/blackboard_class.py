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
