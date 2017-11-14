# Slack bot documentation:
# https://api.slack.com/bot-users

# Slack API documentation:
# https://api.slack.com/web

# Slack API methods:
# https://api.slack.com/methods

# Jinja2 documentation:
# http://jinja.pocoo.org/docs/2.10/api/

# intended workflow:
# - render a template against a gradebook file to create a unique message to send to each student having a row in the gradebook file
# - the resulting messages are then messaged to each user in a Slack Workspace

# cases covered:
# - assignment grades/feedback
# - grade progress reports

# tentative package structure:
# - root folder called virtual_ta
# - local subfolder .env with venv
# - subfolder called tests
# - subfolder called examples
# - subfolder virtual_ta w/ __init__.py, renderers.py, and slackbot.py files
# - __init__.py makes all functions/classes available under virtual_ta
# - renderers.py has a render_template_from_csv_file function that renders a gradebook csv file and a template text file, and returns a dictionary keyed by a specified column
# - slackbot.py has a SlackBot class with a __init__ method having optional API Token parameter, a set_api_token_from_file method requiring a file/file-like object, and a direct_message_users method requiring a dictionary keyed by Slack username

# additional features to consider:
# - posting grades & feedback to a LMS gradebook (provided by adding an LMSBot class?)
# - generating LaTeX schedule table, weekly overview emails (w/ LMS posting via LMSBot?), etc., from Alignment Map Excel file (provided by adding a GradeBook class, which depends upon an Excel file with tabs for students and for each assignment, and/or a relational data store like SQLite? This class could also be used with SlackBot class methods requiring a gradebook Excel file and could have additional gradebook management features)
# - setup GitHub teams/repos within an organization (provided by adding a GitHubBot class relying on GradeBook class and a separate 'github-teams-setup' module?)
# - parsing GitHub PRs for course wiki hw submissions to streamline interweaving and grading (provided by adding a GitHubBot class relying on GradeBook class and a separate 'github-teams-setup' module?)
# - chatops for instructors entering grades and/or students checking grades (spin off into separate module relying on virtual_ta?)

from pprint import pprint
from unittest import TestCase

from virtual_ta import render_template_from_csv_file


class TAWorkflowTests(TestCase):
    def test_send_slack_messages_with_csv_import(self):

        # Prof. X sets up a custom bot user, following the instructions at
        # https://api.slack.com/bot-users to obtain an API Token, which is
        # saved in a file, and set a bot name, icon, full name, description,
        # and allowed IP Address range

        # Prof. X saves a gradebook csv file named with column headings

        # Prof. X saves a template text file as a Jinja2 template, with each
        # variable name a column heading in the gradebook csv file

        # Prof. X uses the render_template_from_csv_file method to render their
        # template file against their gradebook file, returning a dictionary of
        # messages keyed by Slack user name
        with open('examples/example_template.txt') as template_fp:
            with open('examples/example_gradebook.csv') as gradebook_fp:
                template_results = render_template_from_csv_file(
                    template_fp,gradebook_fp,key='Slack_User_Name'
                )

        # Prof. X prints the dictionary to ensure messages are as intended
        pprint(template_results)

        # Prof. X initiates a SlackBot object and then uses the
        # set_api_token_from_file method to load their API Token

        # Prof. X uses the SlackBot direct_message_users method to send the
        # messages in the dictionary to the indicated students
