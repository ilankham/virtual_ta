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
            else:
                api_request_url = None

    def set_team_membership(
            self,
            team_id: Union[int, str],
            user_name: str,
            team_role: str = 'member',
    ) -> Dict[str, str]:
        """Adds or updates membership for existing GitHub Organization team

        Uses the GitHub REST API v3 call
        f'https://api.github.com/teams/{team_id}/memberships/{user_name}'
        with no caching

        Args:
            team_id: id of team within GitHub Organization
            user_name: name of a user to associate with team; if the user is
                not yet a member of the team, they will be invited to join
            team_role: if 'member', then the user is a normal team member; if
                'maintainer', then the user is granted permission to edit the
                team's name/description, to add/remove team members, and to
                promote other team members to team maintainer; defaults to
                'member'

        Returns:
            A dictionary describing the resulting team membership

        """

        return_value = requests.put(
            url=f'https://api.github.com/teams/{team_id}/memberships'
                f'/{user_name}',
            headers={
                'Authorization': f'token {self.personal_access_token}',
                'Content-type': 'application/json',
            },
            json={
                'role': team_role if team_role == 'maintainer' else 'member',
            }
        ).json()
        return return_value

    def create_org_repo(
            self,
            repo_name: str,
            repo_description: str = '',
            repo_homepage: str = '',
            repo_private: bool = False,
            repo_has_issues: bool = True,
            repo_has_projects: bool = True,
            repo_has_wiki: bool = True,
            repo_team_id: str = None,
            repo_auto_init: bool = False,
            repo_gitignore_template: str = '',
            repo_license_template: str = '',
            repo_allow_squash_merge: bool = True,
            repo_allow_merge_commit: bool = True,
            repo_allow_rebase_merge: bool = True,
    ) -> NestedDict:
        """Creates GitHub organization repo with specified properties

        Uses the GitHub REST API v3 call
        f'https://api.github.com/orgs/{self.org_name}/repos'
        with no caching

        Args:
            repo_name: name of repo to create
            repo_description: description of repo to create
            repo_homepage: homepage URL of repo to create
            repo_private: determines whether repo is private; defaults to False
            repo_has_issues: determines whether repo has issues enabled;
                defaults to True
            repo_has_projects: determines whether repo has projects enabled;
                defaults to True
            repo_has_wiki: determines whether repo has its wiki enabled;
                defaults to True
            repo_team_id: id of team within Organization to grant repo access
            repo_auto_init: determines whether repo is initialized with a
                README file; defaults to False
            repo_gitignore_template: language name of .gitignore template to
                include in repo; see https://github.com/github/gitignore for
                language options
            repo_license_template: keyword of license to include in repo; see
                https://help.github.com/articles/licensing-a-repository
                /#searching-github-by-license-type for license options
            repo_allow_squash_merge: determines whether repo allows
                squash-merging pull requests; defaults to True
            repo_allow_merge_commit: determines whether repo allows
                merging pull requests with a merge commit; defaults to True
            repo_allow_rebase_merge: determines whether repo allows
                rebase-merging pull requests; defaults to True

        Returns:
            A dictionary describing the resulting repo

        """

        return_value = requests.post(
            url=f'https://api.github.com/orgs/{self.org_name}/repos',
            headers={
                'Authorization': f'token {self.personal_access_token}',
                'Content-type': 'application/json',
            },
            json={
                'name': repo_name,
                'description': repo_description,
                'homepage': repo_homepage,
                'private': repo_private,
                'has_issues': repo_has_issues,
                'has_projects': repo_has_projects,
                'has_wiki': repo_has_wiki,
                'team_id': repo_team_id,
                'auto_init': repo_auto_init,
                'gitignore_template': repo_gitignore_template,
                'license_template': repo_license_template,
                'allow_squash_merge': repo_allow_squash_merge,
                'allow_merge_commit': repo_allow_merge_commit,
                'allow_rebase_merge': repo_allow_rebase_merge,
            }
        ).json()
        return return_value

    def get_repo_teams(
            self,
            repo_name: str,
    ) -> Generator[Dict[str, Union[int, str]], None, None]:
        """Returns generator of dicts, each describing a repo team affiliation

        Uses the GitHub REST API v3 call
        f'https://api.github.com/repos/{self.org_name}/{repo_name}/teams'
        with no caching and with handling for paging

        Args:
            repo_name: name of existing GitHub repo

        Returns:
            A generator of dictionaries, each describing a team affiliation of
            the GitHub Organization repo

        """

        api_request_url = (
            f'https://api.github.com/repos/{self.org_name}/{repo_name}/teams'
        )

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
