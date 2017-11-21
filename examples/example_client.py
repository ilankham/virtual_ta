from pprint import pprint

from virtual_ta import mail_merge_from_csv_file, SlackAccount

#
# Examples Setup
#

# set API Token for Slack Account
api_token = '[your account API token]'

# initialize Slack Account object
account = SlackAccount(api_token)

#
# Example 1: single hardcoded message to single user
#

# set message parameters for
username = '[username of user to message in corresponding Slack Workspace]'
message = '[message to send to user]'

# send message to user
account.direct_message_by_username({username: message})

#
# Example 2: multiple hardcoded messages to multiple users
#

# set message parameters
messages_to_send = {
    "[first username": "[message to first user]",
    "[second username": "[message to second user]",
    "[third username]": "[message to third user]",
    "[and]": "[so on]"
}

# send messages to users
account.direct_message_by_username(messages_to_send)

#
# Example 3: mail merged messages to multiple users
#

# mail merge example template file against example gradebook file; note: before
# importing the CSV file, the values in the first column, Slack_User_Name
# should be updated with actual user names from the Slack Workspace being used
with open('example_template.txt') as template_fp:
    with open('example_gradebook.csv') as gradebook_fp:
        mail_merge_results = mail_merge_from_csv_file(
            template_fp, gradebook_fp, key='Slack_User_Name'
        )

# print mail merge results
pprint(mail_merge_results)

# send messages to users
account.direct_message_by_username(mail_merge_results)
