import logging
import os
from enum import Enum
from slack_sdk import WebClient
from datetime import datetime

class Action_Value(Enum):
    Approve = 0
    Delete = 1
    RejectDelete = 2

class Button_Style(Enum):
    """Changes the color of the button. Default is gray, Primary is green, Danger is red."""
    default = 0
    primary = 1
    danger = 2

class Slack:
    _MAP_CHANNEL_ID = os.getenv('SLACK_MAP_CHANNEL_ID')
    _TOKEN = os.getenv('SLACK_BOT_TOKEN')

    def __init__(self):
        self._client = WebClient(token=self._TOKEN)
        
    def get_display_name(self, userId: str) -> str:
        user = self._client.users_profile_get(user=userId)
        return user['profile']['display_name_normalized']

    def post_msg_to_channel(self, text: str, blocks: list|None = None, thread_ts: str|None = None, unfurl: bool = False, channel: str = None) -> None:
        if channel is None:
            channel = self._MAP_CHANNEL_ID

        self._client.chat_postMessage(channel=channel, text=text, blocks=blocks, thread_ts=thread_ts, unfurl_links=unfurl, unfurl_media=unfurl)
        logging.info('Posted request to Slack. Done handling.')

    def replace_msg(self, interactivePayload: dict, text: str|None = None, blocks: dict|None = None) -> None:
        channel = interactivePayload['container']['channel_id']
        ts = interactivePayload['container']['message_ts']

        if None == text:
            text = interactivePayload['message']['text']
        
        if None == blocks:
            blocks = interactivePayload['message']['blocks']
        
        self._client.chat_update(channel=channel, ts=ts, blocks=blocks, text=text)
    
    def convert_ts_to_utc(ts: str) -> str:
        return datetime.fromtimestamp(float(ts)).strftime('%y-%m-%d %H:%M:%S UTC')

    def start_blocks() -> list:
        return []


    def get_block_header(message: str) -> dict:
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": message
            }
        }


    def get_block_context(message: str) -> dict:
        return {
            "type": "context",
            "elements": [
                {
                    "type": "plain_text",
                    "text": message
                }
            ]
        }


    def get_block_section(message: str) -> dict:
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message
            }
        }
    

    def get_divider() -> dict:
        return {
            "type": "divider"
        }


    def get_block_actions() -> dict:
        return {
            "type": "actions",
            "block_id": "buttons",
            "elements": []
        }


    def get_block_actions_button(actionBlock: dict, buttonText: str, buttonStyle: Button_Style, buttonValue: str, addConfirmation: bool = False) -> dict:
        button =  {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": buttonText
            },
            "value": buttonValue
        }

        if buttonStyle != Button_Style.default:
            button['style'] = buttonStyle.name

        if addConfirmation:
            button['confirm'] = {
                'title': {
                    'type': 'plain_text',
                    'text': 'Are you sure?'
                },
                'text': {
                    'type': 'plain_text',
                    'text': 'This is reversible, but it is easier if you do not trash this by accident.'
                },
                'confirm': {
                    'type': 'plain_text',
                    'text': 'Yes, trash it'
                },
                'deny': {
                    'type': 'plain_text',
                    'text': 'Nevermind, keep it.'
                }
            }

        actionBlock['elements'].append(button)

        return actionBlock
    
    def replace_buttons(blocks: list, newBlock: dict) -> list:
        """Takes the blocks portion of a message, finds a block with block_id 'buttons' and replaces it with newBlock."""
        
        newBlocks = []

        for block in blocks:
            if block['block_id'] == 'buttons':
                newBlocks.append(newBlock)
            else:
                newBlocks.append(block)
        
        return newBlocks

        