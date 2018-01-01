"""Creates functional tests for project using unittest module

This module assumes the file tests/test_config.ini exists with the following
structure:

[Blackboard]
course_id =
server_address =
application_key =
application_secret =

[GitHub]
organization =
api_token =
user_name =

[Slack]
api_token =

"""

from configparser import ConfigParser
from contextlib import ExitStack
from datetime import date, datetime
from io import StringIO
from unittest import TestCase

from virtual_ta import (
    BlackboardCourse,
    convert_csv_to_multimap,
    convert_xlsx_to_yaml_calendar,
    flatten_dict,
    GitHubOrganization,
    mail_merge_from_csv_file,
    mail_merge_from_yaml_file,
    SlackAccount,
)


class TAWorkflowTests(TestCase):

    def test_post_to_bb_with_csv_import(self):
        # Prof. X follows the instructions at https://community.blackboard.com/
        # docs/DOC-1733-the-blackboard-rest-api-framework to use
        # https://developer.blackboard.com to register an application,
        # recording the Application ID, Application Key, and Application Secret

        # Prof. X uses the Application ID to register a REST API Integration
        # with a Blackboard Learn server, associating the a user account having
        # sufficient access privileges to edit the gradebook for the intended
        # course

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
            grade_feedback_mail_merge_results = mail_merge_from_csv_file(
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
                test_fp.read(),
                flatten_dict(
                    grade_feedback_mail_merge_results,
                    key_value_separator='\n\n-----\n\n',
                    items_separator='\n\n--------------------\n\nMessage to '
                ),
            )

        # Prof. X repeats the same process for grade scores
        with open(
            'examples/example_gradebook-for_testing_blackboard.csv'
        ) as gradebook_fp:
            grade_scores_mail_merge_results = convert_csv_to_multimap(
                gradebook_fp,
                key_column='BB_User_Name',
                values_column='Submission_Complete',
                overwrite_values=True,
            )

        # Prof. X repeats the same process for grade text
        with open(
            'examples/example_gradebook-for_testing_blackboard.csv'
        ) as gradebook_fp:
            grade_text_mail_merge_results = convert_csv_to_multimap(
                gradebook_fp,
                key_column='BB_User_Name',
                values_column='Feedback_Summary',
                overwrite_values=True,
            )

        # Prof. X initiates a BlackboardCourse object by providing their server
        # address, CourseID, Application Key, and Application Secret
        config = ConfigParser()
        config.read('tests/test_config.ini')
        test_bot = BlackboardCourse(
            config['Blackboard']['course_id'],
            config['Blackboard']['server_address'],
            config['Blackboard']['application_key'],
            config['Blackboard']['application_secret'],
        )

        # Prof. X uses the BlackboardCourse create_gradebook_column method to
        # create a column, providing a name, due_date and max_score_possible
        test_column_due_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        test_column_name = 'test_column_created-'+test_column_due_date
        test_bot.create_gradebook_column(
            name=test_column_name,
            due_date=test_column_due_date,
        )

        # Prof. X uses the BlackboardCourse gradebook_column_primary_ids
        # property to verify the column was created
        self.assertIn(
            test_column_name,
            test_bot.gradebook_columns_primary_ids.keys()
        )

        # Prof. X uses the BlackboardCourse update_gradebook_column method to
        # provide the assignment grades and feedback to the indicated students
        # for a specific column by providing a columnID number
        test_bot.set_grades_in_column(
            column_primary_id=test_bot.gradebook_columns_primary_ids[
                test_column_name
            ],
            grades_as_scores=grade_scores_mail_merge_results,
            grades_as_text=grade_text_mail_merge_results,
            grades_feedback=grade_feedback_mail_merge_results,
        )

        # Prof. X uses the BlackboardCourse get_gradebook_column_grades method
        # to verifies assignment grade scores and feedback were correctly added
        for test_user_name in grade_scores_mail_merge_results:
            test_user_grade = test_bot.get_grade(
                column_primary_id=test_bot.gradebook_columns_primary_ids[
                    test_column_name
                ],
                user_name=test_user_name,
            )
            self.assertEqual(
                float(grade_scores_mail_merge_results[test_user_name]),
                float(test_user_grade['score']),
            )
            self.assertEqual(
                grade_feedback_mail_merge_results[test_user_name].strip(),
                test_user_grade['feedback'].strip(),
            )

    def test_github_setup_with_csv_import(self):
        # Prof. X sets up a GitHub Organization and follows the instructions at
        # https://github.com/blog/1509-personal-api-tokens to create a Personal
        # Access Token with scopes admin:org and public_repo

        # Prof. X initiates a GitHubOrganization object associated with their
        # GitHub Organization and their Personal Access Token
        config = ConfigParser()
        config.read('tests/test_config.ini')
        test_bot = GitHubOrganization(
            org_name=config['GitHub']['organization'],
            personal_access_token=config['GitHub']['api_token'],
        )

        # Prof. X uses the GitHubOrganization object to a create team
        test_team_name = 'team-'+datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
        test_team_description = test_team_name+' description'
        test_bot.create_org_team(
            team_name=test_team_name,
            team_description=test_team_description,
            team_privacy='closed'
        )

        # Prof. X checks that the team was created
        self.assertIn(test_team_name, test_bot.org_team_ids.keys())

        # Prof. X uses the GitHubOrganization object adds a member to the team
        test_bot.set_team_membership(
            team_id=test_bot.org_team_ids[test_team_name],
            user_name=config['GitHub']['user_name'],
        )

        # Prof. X checks that the team membership was created
        self.assertIn(
            test_team_name,
            (
                member['login'] for member in test_bot.get_team_membership(
                    test_bot.org_team_ids[test_team_name]
                )
            )
        )

        # Prof. X uses the GitHubOrganization object to create a team repo
        test_repo_name = 'repo-'+datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
        test_repo_description = test_repo_name+' description'
        test_bot.create_team_repo(
            repo_name=test_repo_name,
            team_id=test_bot.org_team_ids[test_team_name],
            repo_permission='push',
            repo_description=test_repo_description,
        )

        # Prof. X checks that the team repo was created
        self.assertIn(
            test_team_name,
            (
                member['name'] for member in test_bot.get_repo_teams(
                    test_bot.org_team_ids[test_team_name]
                )
            )
        )

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
                open(
                    'examples/example_feedback_template-for_testing_slack.txt'
                )
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
                test_fp.read(),
                flatten_dict(
                    mail_merge_results,
                    key_value_separator='\n\n-----\n\n',
                    items_separator='\n\n--------------------\n\nMessage to '
                ),
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

    def test_render_calendar_table(self):
        # Prof. X creates an Excel file with column labels for week number and
        # each day of the week (Monday through Sunday, following ISO 8601),
        # with each cell listing one or more delimited items to be calendared

        # Prof. X uses the generate_calendar_yaml function to create an ordered
        # sequence of nested YAML statements organized by week
        with open('examples/example_calendar_data.xlsx', 'rb') as calendar_fp:
            test_yaml_calendar = convert_xlsx_to_yaml_calendar(
                data_xlsx_fp=calendar_fp,
                start_date=date(2018, 1, 1),
                item_delimiter='|',
                relative_week_number_column='Week',
                worksheet='Assessments',
            )

        # Prof. X prints calendar_yaml to inspect for accuracy
        with open(
            'examples/expected_render_results_for_test_render_calendar_table-'
            'yaml_calendar.yaml'
        ) as test_fp:
            self.assertEqual(
                test_fp.read(),
                test_yaml_calendar,
            )

        # Prof. X saves calendar_yaml to a file for manual editing/updating,
        # including adding comments or additional content
        test_yaml_calendar_fp = StringIO(test_yaml_calendar)

        # Prof. X uses the mail_merge_from_yaml function to create a LaTeX
        # table representation of data_yaml_fp as a dictionary
        with open('examples/example_latex_table_template.tex') as template_fp:
            test_latex_results = mail_merge_from_yaml_file(
                template_fp=template_fp,
                data_yaml_fp=test_yaml_calendar_fp,
            )

        # Prof. X prints a flattened version of the dictionary to verify
        # calendar entries are as intended
        with open(
            'examples/expected_render_results_for_test_render_calendar_table-'
            'latex_table.tex'
        ) as test_fp:
            self.assertEqual(
                test_fp.read(),
                flatten_dict(
                    test_latex_results,
                    key_value_separator='',
                    items_separator='\n'+('%'*80+'\n')*3,
                    suppress_keys=True
                ),
            )
