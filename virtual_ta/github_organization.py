"""Creates a class for interfacing with the GitHub REST API v3

This module encapsulates a GitHub Organization based upon an organization name
and personal access token, with methods for managing organization teams and
repos

See https://developer.github.com/v3/ for more information about the GitHub REST
API v3

"""


class GitHubOrganization(object):
    """Class for interfacing with the GitHub REST API v3"""
    def __init__(self, org_name: str, personal_access_token: str) -> None:
        """Initializes a GitHubOrganization object

        Args:
            org_name: a GitHub organization user name
            personal_access_token: a GitHub personal access token generated
                according to https://github.com/blog/1509-personal-api-tokens

        """

        self.org_name = org_name
        self.personal_access_token = personal_access_token
