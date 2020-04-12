import os
import time
import re
from slackclient import SlackClient
from flask_sqlalchemy import SQLAlchemy


slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
finn_bot_id = None
db = SQLAlchemy(finn_bot)

from models import 
RTM_READ_DELAY = 1
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


def parse_bot_commands(slack_events, counter):
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])

            if "attachments" in event:
                if event["attachments"][0]["author_subname"] == 'BugBot':
                    handle_command('assign', event["channel"], counter)
            elif user_id == finn_bot_id:
                return message, event["channel"]

    return None, None


def parse_direct_mention(message_text):
    matches = re.search(MENTION_REGEX, message_text)

    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(command, channel, counter):
    response = None

    if command.startswith('assign'):
        if len(takers) > 0:
            response = takers[counter]
        else:
            response = "There is no one assigned for taking tasks yet. Use the *add* command followed by a user mention."
        
        if len(takers) > counter + 1:
            counter += 1

    if command.startswith('list'):
        if len(takers) > 0:
            response = takers
        else:
            response = "There is no one assigned for taking tasks yet. Use the *add* command followed by a user mention."

    if command.startswith('add'):
        mention = command.split()[1]

        if mention:
            takers.append(mention)
            response = "{} added to bug squashing squad.".format(mention)
        else:
            response = "Not a valid addition. Try tagging someone."

    if command.startswith('remove'):
        mention = command.split()[1]

        if mention in takers:
            takers.remove(mention)
            response = "{} removed from bug squashing squad.".format(mention)
        else:
            response = "{} is not part of the bug squashing squad.".format(mention)

    slack_client.api_call(
        "chat.postMessage",
        channel = channel,
        text = response,
        as_user = True
    )


if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Finn Bot connected and running!")
        finn_bot_id = slack_client.api_call("auth.test")["user_id"]
        takers = []
        counter = 0

        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read(), counter)
            if command:
                handle_command(command, channel, counter)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
