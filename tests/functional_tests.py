# Slack bot documentation:
# https://api.slack.com/bot-users

# workflow:
# - call gradebot from command line with switches for grade file and template; e.g., gradebot -g gradebook.xlsx -t template.txt
# - completed template is messaged to each user based on their row in grade file

# cases covered:
# - assignment grades/feedback
# - grade progress reports

# additional features to consider:
# - posting to a LMS gradebook
# - parsing GitHub PRs
# - chatops for instructors entering grades and/or students checking grades