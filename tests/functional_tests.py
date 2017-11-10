# Slack bot documentation:
# https://api.slack.com/bot-users

# intended workflow:
# - call gradebot from command line with switches for grade file and template; e.g., gradebot -g gradebook.xlsx -t template.txt
# - completed template is messaged to each user based on their row in grade file

# cases covered:
# - assignment grades/feedback
# - grade progress reports

# additional features to consider:
# - posting grades & feedback to a LMS gradebook
# - parsing GitHub PRs for course wiki hw submissions to streamline interweaving and grading
# - chatops for instructors entering grades and/or students checking grades
# - generating LaTeX schedule table, weekly overview emails, etc., from Alignment Map Excel file



# tentative example workflow:

# Prof. X sets up a custom bot user, following the instructions at https://api.slack.com/bot-users

# Prof. X saves an Excel file named gradebook.xlsx with column headings into a directory

# Prof. X saves a text file named template.txt with {<variable nane>} throughout, with each <variable name> a column heading in an Excel file

# Prof. X saves a config file in YAML format as config.yaml, with all bot parameters needed to make API calls

# Prof. X uses the command line to set the bot config file as gradebot -c config.yaml, which sets environmental variables for all bot parameters

# Prof. X uses the command line to set the bot config file as gradebot -g gradebook.xlsx -t template.

# A text summary is displayed of what will be sent to whom and output to an ISO 8661 datetime-stamped file with name template-completed-datetime-stamp.txt

# A prompt is then given to send or cancel

# Prof. X chooses send, and messages are sent as the bot user specified in config.yaml