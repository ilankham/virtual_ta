from contextlib import ExitStack
from datetime import datetime
from pprint import pprint

from virtual_ta import (
    BlackboardCourse,
    convert_csv_to_multimap,
    mail_merge_from_csv_file,
    SlackAccount,
)

###############################################################################
#
# Blackboard Course Examples
#
###############################################################################

# set parameters for Blackboard Course
course_id = '[your course id]'
server_address = '[your server address]'
application_key = '[your application key]'
application_secret = '[your application secret]'

# initialize Blackboard Course object
course = BlackboardCourse(
    course_id,
    server_address,
    application_key,
    application_secret,
)


#
# Blackboard Example 1: print all gradebook columns in the course
#

pprint(list(course.gradebook_columns))


#
# Blackboard Example 2: create a gradebook column
#

# set gradebook column parameters
column_due_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
column_name = 'test_column_created-'+column_due_date
column_description = column_name+' description'
column_max_score_possible = 100
column_available_to_students = 'Yes'
column_grading_type = 'Manual'

# create gradebook column with specified parameters, printing result
pprint(course.create_gradebook_column(
    name=column_name,
    due_date=column_due_date,
    description=column_description,
    max_score_possible=column_max_score_possible,
    available_to_students=column_available_to_students,
    grading_type=column_grading_type,
))


#
# Blackboard Example 3: get a single grade from a gradebook column
#

# set parameters for grade to retrieve, using the column created in Example 2
column_primary_id = course.gradebook_columns_primary_ids[column_name]
user_name = '[user name to get grade for]'

# print corresponding grade
pprint(course.get_grade(
    column_primary_id=column_primary_id,
    user_name=user_name,
))


#
# Blackboard Example 4: get all grades in a gradebook column
#

# set parameters for grades to retrieve, using the column created in Example 2
column_primary_id = course.gradebook_columns_primary_ids[column_name]

# print corresponding grades
pprint(course.get_grades_in_column(
    column_primary_id=column_primary_id,
))


#
# Blackboard Example 5A: set a single grade with overwrite on
#

# set parameters for grade to enter, using the column created in Example 2
column_primary_id = course.gradebook_columns_primary_ids[column_name]
user_name = '[user name to set grade for]'
grade_as_score = 95
grade_feedback = 'Good Work!'

# set grade with specified parameters, printing result
pprint(course.set_grade(
    column_primary_id=column_primary_id,
    user_name=user_name,
    grade_as_score=grade_as_score,
    grade_feedback=grade_feedback,
    overwrite=True
))


#
# Blackboard Example 5B: set a single grade with overwrite off
#

# set parameters for grade to enter, using the column created in Example 2
column_primary_id = course.gradebook_columns_primary_ids[column_name]
user_name = '[user name to set grade for]'
grade_as_score = 65
grade_feedback = 'Less Than Good Work!'

# set grade with specified parameters, printing result; assuming the same user
# name is used as in Example 5A, the overwrite=False setting means the results
# should be identical to Example 4A since the user's grade in the column
# already exists
pprint(course.set_grade(
    column_primary_id=column_primary_id,
    user_name=user_name,
    grade_as_score=grade_as_score,
    grade_feedback=grade_feedback,
    overwrite=False
))


#
# Blackboard Example 6: set multiple mail-merged grades in a gradebook column
#

# set parameters for grades to enter, using the column created in Example 2 and
# mail merging the example template file against the example gradebook file to
# create grade scores (taking the last-appearing score for each user, per the
# overwrite_values=True parameter) and to create grade feedback
#
# Note: before importing the CSV file, the values in the first column,
# BB_User_Name, should be updated with actual user names from your Blackboard
# Course
column_primary_id = course.gradebook_columns_primary_ids[column_name]
with ExitStack() as es:
    template_fp = es.enter_context(
        open('example_feedback_template-for_testing_blackboard.txt')
    )
    gradebook_fp = es.enter_context(
        open('example_gradebook-for_testing_blackboard.csv')
    )
    grade_scores_mail_merge_results = convert_csv_to_multimap(
        gradebook_fp,
        key_column='BB_User_Name',
        values_column='Submission_Complete',
        overwrite_values=True,
    )
    grade_feedback_mail_merge_results = mail_merge_from_csv_file(
        template_fp,
        gradebook_fp,
        key='BB_User_Name',
    )

# set grades with specified parameters, printing results
pprint(course.set_grades_in_column(
    column_primary_id=column_primary_id,
    grades_as_scores=grade_scores_mail_merge_results,
    grades_feedback=grade_feedback_mail_merge_results,
))


###############################################################################
#
# Slack Account Examples
#
###############################################################################

# set API Token for Slack Account
api_token = '[your account API token]'

# initialize Slack Account object
account = SlackAccount(api_token)


#
# Slack Example 1: send a single, hardcoded message to a single user
#

# set message parameters
username = '[username of user to message in corresponding Slack Workspace]'
message = '[message to send to user]'

# send message to user
account.direct_message_by_username({username: message})


#
# Slack Example 2: send multiple hardcoded messages to multiple users
#

# set message parameters
messages_to_send = {
    '[first username]': '[message to first user]',
    '[second username]': '[message to second user]',
    '[third username]': '[message to third user]',
    '[and]': '[so on]'
}

# send messages to users
account.direct_message_by_username(messages_to_send)


#
# Slack Example 3: send mail-merged messages to multiple users
#

# set parameters for messages to send, mail merging the example template file
# against the example gradebook file
#
# Note: before importing the CSV file, the values in the first column,
# Slack_User_Name, should be updated with actual user names from your
# Slack Workspace
with ExitStack() as es:
    template_fp = es.enter_context(
        open('example_feedback_template-for_testing_slack.txt')
    )
    gradebook_fp = es.enter_context(
        open('example_gradebook-for_testing_slack.csv')
    )
    mail_merge_results = mail_merge_from_csv_file(
        template_fp,
        gradebook_fp,
        key='Slack_User_Name',
    )

# print mail merge results
pprint(mail_merge_results)

# send messages to users
account.direct_message_by_username(mail_merge_results)


#
# Slack Example 4: create and setup a public channel, inviting multiple users
#

# set parameters for channel to setup, inviting the users in the mail merging
# results from the above example
channel_name = datetime.now().strftime('channel%Y%m%d%H%M%S')
users_to_invite = mail_merge_results.keys()
channel_purpose = datetime.now().strftime('Test Channel Purpose')
channel_topic = datetime.now().strftime('Test Channel Topic')
account.create_and_setup_channel(
    channel_name=channel_name,
    user_names_to_invite=users_to_invite,
    channel_purpose=channel_purpose,
    channel_topic=channel_topic,
    public=True,
)


#
# Slack Example 5: create and setup a private channel, inviting multiple users
#

# set parameters for channel to setup, inviting the users in the mail merging
# results from the above example
channel_name = datetime.now().strftime('channel%Y%m%d%H%M%S')
users_to_invite = mail_merge_results.keys()
channel_purpose = datetime.now().strftime('Test Channel Purpose')
channel_topic = datetime.now().strftime('Test Channel Topic')
account.create_and_setup_channel(
    channel_name=channel_name,
    user_names_to_invite=users_to_invite,
    channel_purpose=channel_purpose,
    channel_topic=channel_topic,
    public=False,
)
