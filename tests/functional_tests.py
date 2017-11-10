# Slack bot documentation:
# https://api.slack.com/bot-users

# intended workflow:
# - render a template against a gradebook file to create a unique message to send to each student having a row in the gradebook file
# - the resulting messages are then messaged to each user in Slack

# cases covered:
# - assignment grades/feedback
# - grade progress reports

# additional features to consider:
# - posting grades & feedback to a LMS gradebook
# - chatops for instructors entering grades and/or students checking grades
# - generating LaTeX schedule table, weekly overview emails (w/ LMS posting?), etc., from Alignment Map Excel file (spin off into separate module?)
# - setup GitHub teams/repos within an organization (spin off into separate 'github-team-setup' module?)
# - parsing GitHub PRs for course wiki hw submissions to streamline interweaving and grading (spin off into separate 'github-team-setup' module?)



# tentative example workflow:

# Prof. X sets up a custom bot user, following the instructions at https://api.slack.com/bot-users

# Prof. X saves an Excel file named gradebook.xlsx with column headings into a directory

# Prof. X saves a text file named template.txt with {<variable nane>} throughout, with each <variable name> a column heading in an Excel file

# Prof. X saves a config file in YAML format as config.yaml, with all bot parameters needed to make API calls

# Prof. X initiates a bot class object using the config file

# Prof. X uses a bot class method to render the template file against the gradebook file, returning a dictionary of messages keyed by Slack user name

# Prof. X prints the dictionary to ensure messages are as intended

# Prof. X uses a bot class method to send the messages to all students indicated in the dictionary