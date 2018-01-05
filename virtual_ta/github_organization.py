"""Creates a class for interfacing with the GitHub REST API v3

This module encapsulates a GitHub Organization based upon an organization name
and personal access token, with methods for managing organization teams and
repos

See https://developer.github.com/v3/ for more information about the GitHub REST
API v3

"""

import re
import requests
from typing import Dict, Generator, List, Union

NestedDict = Dict[
    str,
    Union[bool, Dict[str, Union[bool, int, None, str]], int, None, str]
]


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

    @property
    def org_team_ids(self) -> Dict[str, int]:
        """Returns a dict with team name -> team id

        Uses the GitHub REST API v3 with no caching

        """

        return {
            team['name']: team['id'] for team in self.org_teams
        }

    def create_org_team(
            self,
            team_name: str,
            team_description: str = '',
            team_maintainers: List[str] = None,
            team_repo_names: List[str] = None,
            team_privacy: str = 'secret',
    ) -> NestedDict:
        """Creates GitHub organization team with specified properties

        Uses the GitHub REST API v3 call
        f'https://api.github.com/orgs/{self.org_name}/teams'
        with no caching

        Args:
            team_name: display name of team to create
            team_description: display description of team to create
            team_maintainers: list of login names for team maintainers
            team_repo_names: list of repo names to add to team in the format
                'org_name/repo_name'
            team_privacy: if 'secret', then the team is visible to organization
                owners and team members; if 'closed', then the team is visible
                to all organization members; defaults to 'secret'

        Returns:
            A dictionary describing the resulting gradebook column

        """

        if team_maintainers is None:
            team_maintainers = []
        if team_repo_names is None:
            team_repo_names = []

        return_value = requests.post(
            url=f'https://api.github.com/orgs/{self.org_name}/teams',
            headers={
                'Authorization': f'token {self.personal_access_token}',
                'Content-type': 'application/json',
            },
            json={
                'name': team_name,
                'description': team_description,
                'maintainers': team_maintainers,
                'repo_names': team_repo_names,
                'privacy': team_privacy
                if team_privacy == 'closed' else 'secret',
            }
        ).json()
        return return_value

    def get_team_membership(
            self,
            team_id: Union[int, str],
    ) -> Generator[Dict[str, Union[int, str]], None, None]:
        """Returns a generator of dicts, each describing an org team member

        Uses the GitHub REST API v3 call
        f'https://api.github.com/teams/{team_id}/members/'
        with no caching and with handling for paging

        Args:
            team_id: id of team within GitHub Organization

        Returns:
            A generator of dictionaries, each describing a member of the GitHub
            Organization team

        """

        api_request_url = f'https://api.github.com/teams/{team_id}/members'

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
                print(api_request_url)
            else:
                api_request_url = None
