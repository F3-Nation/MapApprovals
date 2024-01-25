import logging
import os
from enum import Enum, auto
from slack_sdk import WebClient
from datetime import datetime
import pytz

class Action_Value(Enum):
    Approve = auto()
    Refresh = auto()
    MarkComplete = auto()
    Delete = auto()
    RejectDelete = auto()
    Edit = auto()

class Views(Enum):
    EditWorkout = auto()


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

    def get_msg(self, ts: str, channel: str|None = None) -> dict:
        channel = channel or self._MAP_CHANNEL_ID
        response = self._client.conversations_history(channel=channel, inclusive=True, oldest=ts, limit=1)
        a = response['messages']
        return response['messages'][0]
    
    def post_msg_to_channel(self, text: str, blocks: list|None = None, thread_ts: str|None = None, unfurl: bool = False, channel: str = None) -> None:
        if channel is None:
            channel = self._MAP_CHANNEL_ID

        self._client.chat_postMessage(channel=channel, text=text, blocks=blocks, thread_ts=thread_ts, unfurl_links=unfurl, unfurl_media=unfurl)
        logging.info('Posted request to Slack. Done handling.')

    def replace_msg(self, original_message: dict, ts: str, channel: str|None = None, text: str|None = None, blocks: dict|None = None) -> None:
        channel = channel or self._MAP_CHANNEL_ID
        text = text or original_message['text']
        blocks = blocks or original_message['blocks']

        self._client.chat_update(channel=channel, ts=ts, blocks=blocks, text=text)
    
    def open_modal(self, view_id: str, interactivePayload: dict, title: str, blocks: list, cancelText: str|None = None, submit_text: str|None = None, notify_on_close: bool = False, external_id: str|None = None) -> None:
        """Will open a modal on the user's screen.
        
        Certain fields cannot have more than 24 characters.
        """
        view = {
            "type": "modal",
            "callback_id": view_id,
            "title": {
                "type": 'plain_text',
                "text": title[:24]
            },
            "submit": {
                "type": "plain_text",
                "text": submit_text[:24] or "Submit"
            },
            "close": {
                "type": "plain_text",
                "text": cancelText[:24] or "Cancel"
            },
            "notify_on_close": False,
            "external_id": external_id or "",
            "blocks": blocks
        }
        
        self._client.views_open(trigger_id=interactivePayload['trigger_id'], view=view)
    
    def convert_ts_to_et(ts: str) -> str:
        """Takes the Slack timestamp, which is in UTC Epoch, and converts it to a string based in Eastern Time."""
        
        return datetime.fromtimestamp(float(ts)).astimezone(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S ET')

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
    
    def get_block_input(id: str, label: str, initial_value: str|None = None, optional: bool = True, multiline: bool = False) -> dict:
        return {
			"type": "input",
			"block_id": id,
			"label": {
				"type": "plain_text",
				"text": label
			},
			"element": {
				"type": "plain_text_input",
				"initial_value": initial_value,
				"action_id": id,
                "multiline": multiline
			},
			"optional": optional
		}
    
    def replace_buttons(blocks: list, newBlock: dict) -> list:
        """Takes the blocks portion of a message, finds a block with block_id 'buttons' and replaces it with newBlock."""
        
        newBlocks = []

        for block in blocks:
            if block['block_id'] == 'buttons':
                newBlocks.append(newBlock)
            else:
                newBlocks.append(block)
        
        return newBlocks