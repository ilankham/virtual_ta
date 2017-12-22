"""Create functional tests for project using unittest module

This module assumes the file tests/test_config.ini exports the following:

[Slack]
api_token =

[Blackboard]
application_key =
application_secret =
server_address =
course_id =

[GitHub]
api_token =

"""

from configparser import ConfigParser
from contextlib import ExitStack
from datetime import date
from io import StringIO
from unittest import TestCase

from virtual_ta import (
    BlackboardClass,
    flatten_dict,
    convert_csv_to_multimap,
    convert_xlsx_to_yaml_calendar,
    mail_merge_from_csv_file,
    mail_merge_from_yaml_file,
    SlackAccount,
)


class TAWorkflowTests(TestCase):
    def test_send_slack_messages_with_csv_import(self):
        # For the intended Slack Workspace and the user account from which they
        # wish to have messages originate, Prof. X creates an API Token by
        # (1) visiting https://api.slack.com/custom-integrations/legacy-tokens
        #     and generating a Legacy Token, or
        # (2) visiting https://api.slack.com/apps and creating a new app with
        #     permission scopes for chat:write:user, im:read, and users:read

        # Prof. X saves a gradebook csv file named with column headings and one
        # row per student grade record; columns include Slack_User_Name

        # Prof. X saves a template text file as a Jinja2 template, with each
        # variable name a column heading in the gradebook csv file

        # Prof. X uses the mail_merge_from_csv_file method to mail merge their
        # template file against their gradebook file, returning a dictionary of
        # messages keyed by Slack user name
        with ExitStack() as es:
            template_fp = es.enter_context(
                open('examples/example_feedback_template-for_testing_slack.txt')
            )
            gradebook_fp = es.enter_context(
                open('examples/example_gradebook-for_testing_slack.csv')
            )
            mail_merge_results = mail_merge_from_csv_file(
                template_fp,
                gradebook_fp,
                key='Slack_User_Name',
            )

        # Prof. X prints a flattened version of the dictionary to verify
        # message contents are as intended
        with open(
            'examples/expected_render_results_for_test_send_slack_messages'
            '_with_csv_import.txt'
        ) as test_fp:
            self.assertEqual(
                flatten_dict(
                    mail_merge_results,
                    key_value_separator="\n\n-----\n\n",
                    items_separator="\n\n--------------------\n\nMessage to "
                ),
                test_fp.read()
            )

        # Prof. X initiates a SlackAccount object using their API Token
        config = ConfigParser()
        config.read('tests/test_config.ini')
        test_bot = SlackAccount(config['Slack']['api_token'])

        # Prof. X uses the SlackAccount direct_message_users method to send the
        # messages in the dictionary to the indicated students
        test_bot.direct_message_by_username(mail_merge_results)

        # Prof. X verifies in the Slack Workspace corresponding to their API
        # Token direct messages have been send with themselves as the sender

    def test_post_to_bb_with_csv_import(self):
        # Prof. X follows the instructions at https://community.blackboard.com/
        # docs/DOC-1733-the-blackboard-rest-api-framework to use
        # https://developer.blackboard.com to register an application,
        # recording the Application ID, Application Key, and Application Secret

        # Prof. X uses the Application ID to register a REST API Integration
        # with a Blackboard Learn server, associating the a user account having
        # sufficient access privileges to edit the gradebook for the intended
        # class

        # Prof. X saves a gradebook specification csv file with column
        # headings and one row per gradebook column

        # Prof. X saves a gradebook csv file for one gradebook column with
        # column headings and one row per student grade record

        # Prof. X saves a template text file as a Jinja2 template, with each
        # variable name a column heading in the gradebook csv file

        # Prof. X uses the mail_merge_from_csv_file method to mail merge their
        # template file against their gradebook file, returning a dictionary of
        # assignment feedback keyed by Blackboard user name
        with ExitStack() as es:
            template_fp = es.enter_context(
                open('examples/example_feedback_template-'
                     'for_testing_blackboard.txt')
            )
            gradebook_fp = es.enter_context(
                open('examples/example_gradebook-for_testing_blackboard.csv')
            )
            assignment_feedback_mail_merge_results = mail_merge_from_csv_file(
                template_fp,
                gradebook_fp,
                key='BB_User_Name',
            )

        # Prof. X prints a flattened version of the dictionary to verify
        # assignment feedback contents are as intended
        with open(
            'examples/expected_render_results_for_test_post_to_bb_with_csv'
            '_import.txt'
        ) as test_fp:
            self.assertEqual(
                flatten_dict(
                    assignment_feedback_mail_merge_results,
                    key_value_separator="\n\n-----\n\n",
                    items_separator="\n\n--------------------\n\nMessage to "
                ),
                test_fp.read()
            )

        # Prof. X repeats the same process for assignment grades
        with open(
            'examples/example_gradebook-for_testing_blackboard.csv'
        ) as gradebook_fp:
            assignment_grades_mail_merge_results = convert_csv_to_multimap(
                gradebook_fp,
                key_column='BB_User_Name',
                values_column='Submission_Complete',
                overwrite_values=True,
            )

        # Prof. X initiates a BlackboardClass object by providing their server
        # address, CourseID, Application Key, and Application Secret
        config = ConfigParser()
        config.read('tests/test_config.ini')
        test_bot = BlackboardClass(
            config['Blackboard']['server_address'],
            config['Blackboard']['course_id'],
            config['Blackboard']['application_key'],
            config['Blackboard']['application_secret'],
        )
        self.fail('Finish the test!')

        # Prof. X uses the BlackboardClass create_gradebook_columns method to
        # setup the Blackboard gradebook using the prepared file

        # Prof. X uses the BlackboardClass gradebook_columns property to verify
        # the Blackboard gradebook was properly setup

        # Prof. X uses the BlackboardClass update_gradebook_column method to
        # provide the assignment grades and feedback to the indicated students
        # for a specific column by providing a columnID number
        test_bot.update_gradebook_column_by_username(
            column_id=config['Blackboard']['column_id'],
            assignment_grades=assignment_grades_mail_merge_results,
            assignment_feedback=assignment_feedback_mail_merge_results,
        )

        # Prof. X verifies the assignment feedback was correctly added by
        # manually inspecting the corresponding BB Gradebook

    def test_render_calendar_table(self):
        # Prof. X creates an Excel file with column labels for week number and
        # each day of the week (Monday through Sunday, following ISO 8601),
        # with each cell listing one or more delimited items to be calendared

        # Prof. X uses the generate_calendar_yaml function to create an ordered
        # sequence of nested YAML statements organized by week
        with open('examples/example_calendar_data.xlsx', 'rb') as calendar_fp:
            yaml_calendar = convert_xlsx_to_yaml_calendar(
                data_xlsx_fp=calendar_fp,
                start_date=date(2018, 1, 1),
                item_delimiter='|',
                week_number_column='Week',
                worksheet='Assessments',
            )

        # Prof. X prints calendar_yaml to inspect for accuracy
        with open(
            'examples/expected_render_results_for_test_render_calendar_table-'
            'yaml_calendar.yaml'
        ) as test_fp:
            self.assertEqual(
                yaml_calendar,
                test_fp.read()
            )

        # Prof. X saves calendar_yaml to a file for manual editing/updating,
        # including adding comments or additional content
        data_yaml_fp = StringIO(yaml_calendar)

        # Prof. X uses the mail_merge_from_yaml function to create a LaTeX
        # table representation of data_yaml_fp as a dictionary
        with open('examples/example_latex_table_template.tex') as template_fp:
            latex_results = mail_merge_from_yaml_file(
                template_fp=template_fp,
                data_yaml_fp=data_yaml_fp,
            )

        # Prof. X prints a flattened version of the dictionary to verify
        # calendar entries are as intended
        with open(
            'examples/expected_render_results_for_test_render_calendar_table-'
            'latex_table.tex'
        ) as test_fp:
            self.assertEqual(
                flatten_dict(
                    latex_results,
                    key_value_separator="",
                    items_separator='\n'+('%'*80+'\n')*3,
                    suppress_keys=True
                ),
                test_fp.read()
            )

    def test_github_setup_with_csv_import(self):
        # Prof. X sets up a GitHub Organization and follows the instructions at
        # https://github.com/blog/1509-personal-api-tokens to create a Personal
        # API Token with scopes admin:org and public_repo

        # Prof. X saves the API Token in a text file

        # Prof. X saves a gradebook csv file named with column headings and
        # one row per student grade record; columns include GitHub_User_Name
        # and Team_Number

        # Prof. X reads in the gradebook and creates a dictionary keyed by
        # Team_Number and values comprising lists of corresponding
        # GitHub_User_Name values
        with open(
            'examples/example_gradebook-for_testing_github.csv'
        ) as gradebook_fp:
            team_assignments = convert_csv_to_multimap(
                gradebook_fp,
                key_column='Team_Number',
                values_column='GitHub_User_Name',
                overwrite_values=False,
            )
            print(team_assignments)

        # Prof. X initiates a GitHubOrganization object associated with their
        # GitHub Organization and their API Token
        config = ConfigParser()
        config.read('tests/test_config.ini')
        self.fail('Finish the test!')

        # Prof. X uses the GitHubOrganization object to create teams within the
        # GitHub Organization

        # Prof. X uses the GitHubOrganization object to create project repos
        # for each team
