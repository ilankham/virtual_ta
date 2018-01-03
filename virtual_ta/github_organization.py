"""Creates a class for interfacing with the GitHub REST API v3

This module encapsulates a GitHub Organization based upon an organization name
and personal access token, with methods for managing organization teams and
repos

See https://developer.github.com/v3/ for more information about the GitHub REST
API v3

"""

import re
import requests
from typing import Dict, Generator, Union


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

    @property
    def org_teams(self) -> Generator[Dict[str, Union[int, str]], None, None]:
        """Returns a generator of dicts, each describing an organization team

        Uses the GitHub REST API v3 call
        f'https://api.github.com/orgs/{self.org_name}/teams'
        with no caching and with handling for paging

        """

        api_request_url = f'https://api.github.com/orgs/{self.org_name}/teams'

        while api_request_url:
            api_response = requests.get(
                api_request_url,
                headers={
                    'Authorization': f'token {self.personal_access_token}',
                },
            )
            yield from api_response.json()
            paging_navigation_header = api_response.headers.get('Link', '')
            if 'rel="next"' in paging_navigation_header:
                api_request_url = re.search(
                    '<.*?>',
                    paging_navigation_header
                ).group()[1:-1]
            else:
                api_request_url = None
