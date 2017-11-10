# Slack bot documentation:
# https://api.slack.com/bot-users

# intended workflow:
# - render a template against a gradebook file to create a unique message to send to each student having a row in the gradebook file
# - the resulting messages are then messaged to each user in Slack

# cases covered:
# - assignment grades/feedback
# - grade progress reports

# tentative package structure:
# - root folder called gradesbot
# - local subfolder .env with venv
# - subfolder called tests
# - subfolder called examples
# - subfolder gradesbot w/ __init__.py making SlackBot class available
# - SlackBot class has __init__ method requiring a config file to be provided, render method requiring gradebook and template files to be provided with a dictionary keyed by Slack username returned, and a message users method requiring a dictionary keyed by Slack username

# additional features to consider:
# - posting grades & feedback to a LMS gradebook (provided by adding an LMSBot class?)
# - generating LaTeX schedule table, weekly overview emails (w/ LMS posting via LMSBot?), etc., from Alignment Map Excel file (provided by adding a GradeBook class, which depends upon an Excel file with tabs for students and for each assignment, and/or a relational data store like SQLite? This class could also be used with SlackBot class methods requiring a gradebook Excel file and could have additional gradebook management features)
# - setup GitHub teams/repos within an organization (provided by adding a GitHubBot class relying on GradeBook class and a separate 'github-teams-setup' module?)
# - parsing GitHub PRs for course wiki hw submissions to streamline interweaving and grading (provided by adding a GitHubBot class relying on GradeBook class and a separate 'github-teams-setup' module?)
# - chatops for instructors entering grades and/or students checking grades (spin off into separate module relying on gradesbot?)



# tentative example workflow:

# Prof. X sets up a custom bot user, following the instructions at https://api.slack.com/bot-users

# Prof. X saves an Excel file named gradebook.xlsx with column headings into a directory

# Prof. X saves a text file named template.txt with {<variable nane>} throughout, with each <variable name> a column heading in an Excel file

# Prof. X saves a config file in YAML format as config.yaml, with all bot parameters needed to make API calls

# Prof. X initiates a bot class object using the config file

# Prof. X uses a bot class method to render the template file against the gradebook file, returning a dictionary of messages keyed by Slack user name

# Prof. X prints the dictionary to ensure messages are as intended

# Prof. X uses a bot class method to send the messages to all students indicated in the dictionary