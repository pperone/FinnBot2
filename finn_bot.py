import os
import time
import re

from slackclient import SlackClient

from sqlalchemy import create_engine  
from sqlalchemy import Column, String, Integer, ARRAY
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker


# Database creation and setup
engine = create_engine(os.environ['DATABASE_URL'])
base = declarative_base()

class Team(base):  
    __tablename__ = 'teams'

    channel = Column(String, primary_key=True)
    users = Column(String)
    current = Column(Integer)

Session = sessionmaker(engine)  
session = Session()

base.metadata.create_all(engine)


# Slack setup
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
finn_bot_id = None


# Constants
RTM_READ_DELAY = 1
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


def create_team(channel):
    team = Team(channel=channel, users='', current=0)
    session.add(Team(channel=channel, users='', current=0))
    session.commit()
    return team


def get_team(channel):
    team = session.query(Team).filter_by(channel=channel).first()
    return team


# Create team if it doesn't exist, retrieve it if it does
def evaluate_team(channel):
    team = get_team(channel)

    if team:
        channel = team.channel
        counter = team.current
        users = team.users
    else:
        team = create_team(channel)
        channel = team.channel
        counter = team.current
        users = team.users
    
    return team, channel, counter, users


def parse_bot_commands(slack_events):
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            team, channel, counter, users = evaluate_team(event["channel"])

            if "attachments" in event:
                if event["attachments"][0]["author_subname"] == 'BugBot':
                    handle_command('assign', team)
            elif user_id == finn_bot_id:
                handle_command(message, team)

    return None, None


# Extract direct mention to bot
def parse_direct_mention(message_text):
    matches = re.search(MENTION_REGEX, message_text)

    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


# All the possible commands from user input
def handle_command(command, team):
    response = None
    users = team.users.split()

    if command.startswith('assign'):
        if len(users) <= team.current + 1:
            team.current = 0

        if len(users) > 0:
            response = users[team.current]
            team.current += 1
        else:
            response = "There is no one assigned for taking tasks yet. Use the *add* command followed by a user mention."

    if command.startswith('list'):
        if len(users) > 0:
            response = users
        else:
            response = "There is no one assigned for taking tasks yet. Use the *add* command followed by a user mention."

    if command.startswith('increase'):
        if len(users) > team.current + 1:
            team.current += 1
            response = "Position in queue moved forward by one person"
        elif len(users) > 1:
            team.current = 0
            response = "Position in queue moved forward by one person"
        else:
            response = "Queue position can\'t be moved"

    
    if command.startswith('decrease'):
        if team.current > 0:
            team.current -= 1
            response = "Position in queue moved backward by one person"
        elif len(users) > 1:
            team.current = len(users) - 1
            response = "Position in queue moved backward by one person"
        else:
            response = "Queue position can\'t be moved"


    if command.startswith('current'):
        response = "Queue position is currently *{}*.".format(team.current)


    if command.startswith('add'):
        mention = command.split()[1]

        if mention:
            team.users += " " + mention
            response = "{} added to bug squashing squad.".format(mention)
        else:
            response = "Not a valid addition. Try tagging someone."

    if command.startswith('remove'):
        mention = command.split()[1]

        if mention in users:
            remove = " " + mention
            updated = team.users.replace(remove, '')
            team.users = updated
            response = "{} removed from bug squashing squad.".format(mention)
        else:
            response = "{} is not part of the bug squashing squad.".format(mention)

        if team.current >= len(users):
            team.current -= 1

    slack_client.api_call(
        "chat.postMessage",
        channel = team.channel,
        text = response,
        as_user = True
    )

    session.commit()


if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Finn Bot connected and running!")
        finn_bot_id = slack_client.api_call("auth.test")["user_id"]

        while True:
            parse_bot_commands(slack_client.rtm_read())
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
