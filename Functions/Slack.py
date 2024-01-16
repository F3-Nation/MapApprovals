import logging
from enum import Enum
import os
from slack_sdk import WebClient
from Functions.Shared import (
    getEntry,
    updateEntry,
    trashGravityFormsEntry,
    sendEmail,
)


ActionValue = Enum('ActionValue', ['Approve', 'Delete', 'RejectDelete'])
class ButtonStyle(Enum):
    """Changes the color of the button. Default is gray, Primary is green, Danger is red."""
    default = 0
    primary = 1
    danger = 2

class Slack:
    MAP_CHANNEL_ID = os.getenv('SLACK_MAP_CHANNEL_ID')

    def __init__(self, token):
        self.token = token
        self.client = WebClient(token=token)

    def get_display_name(self, userId: str) -> str:
        user = self.client.users_profile_get(user=userId)
        return user['profile']['display_name_normalized']

    def handle_slack_action(self, body: dict):
        logging.debug(body)
        logging.info('Handling Slack Action.')

        actionValue = body['actions'][0]['value']
        logging.debug('Action value: ' + body['actions'][0]['value'])
        actionValuePieces = str.split(actionValue, '_')
        action = actionValuePieces[0]
        entryId = actionValuePieces[1]
        user = self.get_display_name(body['user']['id'])

        if action == ActionValue.Approve.name:
            logging.info('Action: Approve')
            entry = getEntry(entryId)
            entry['is_approved'] = "1"
            entry['is_read'] = "1"

            submissionType = self._is_new_or_update(entry)

            logging.info('For entry ' + entryId + ', set is_approved and is_read to 1. Updating entry.')
            success = updateEntry(entryId, entry)
            if success:
                self.post_msg_to_channel(text='Map Request approved by ' + user + '.', thread_ts=body['container']['message_ts'])
                sendEmail('Map Request Approved', [entry['19']], '<div style="display: none; max-height: 0px; overflow: hidden;">' + submissionType + ' -> ' + entry['2'] + ' @ ' + entry['21'] + '</div><div style="display: none; max-height: 0px; overflow: hidden;">&#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy;</div><p>Your map request has been approved and should show up on <a href="https://map.f3nation.com">the map</a> within the hour. If you see a mistake, use this <a href="' + os.getenv('GRAVITY_FORMS_BASE_URL') + '/wp-admin/admin.php?page=gf_entries&view=entry&screen_mode=edit&id=' + os.getenv('GRAVITY_FORM_WORKOUT_FORM_ID') + '&lid=' + entry['id'] + '">link</a> to submit a correction. Reply to this email with any other issues.</p><table border="1" style="border-collapse:collapse" cellpadding="5"><tr><td><b>Region</b></td><td>' + entry['21'] + '</td></tr><tr><td><b>Workout Name</b></td><td>' + entry['2'] + '</td></tr><tr><td><b>Street 1</b></td><td>' + entry['1.1'] + '</td></tr><tr><td><b>Street 2</b></td><td>' + entry['1.2'] + '</td></tr><tr><td><b>City</b></td><td>' + entry['1.3'] + '</td></tr><tr><td><b>State</b></td><td>' + entry['1.4'] + '</td></tr><tr><td><b>ZIP Code</b></td><td>' + entry['1.5'] + '</td></tr><tr><td><b>United States</b></td><td>' + entry['1.6'] + '</td></tr><tr><td><b>Latitude</b></td><td>' + entry['13'] + '</td></tr><tr><td><b>Longitude</b></td><td>' + entry['12'] + '</td></tr><tr><td><b>Weekday</b></td><td>' + entry['14'] + '</td></tr><tr><td><b>Time</b></td><td>' + entry['4'] + '</td></tr><tr><td><b>Type</b></td><td>' + entry['5'] + '</td></tr><tr><td><b>Region Website</b></td><td>' + entry['17'] + '</td></tr><tr><td><b>Region Logo</b></td><td>' + entry['16'] + '</td></tr><tr><td><b>Notes</b></td><td>' + entry['15'] + '</td></tr><tr><td><b>Submitter</b></td><td>' + entry['18'] + '</td></tr><tr><td><b>Submitter Email</b></td><td>' + entry['19'] + '</td></tr><tr><td><b>Request Created</b></td><td>' + entry['date_created'] + ' UTC</td></tr><tr><td><b>Request Updated</b></td><td>' + entry['date_updated'] + ' UTC</td></tr></table>')
                logging.info('Entry updated, action logged to Slack thread, requestor emailed.')
            else:
                logging.error('Could not approve entry ' + entryId)
                self.post_msg_to_channel(text='Map Request Approval Failed! ' + user + ' tried to approve it, the system failed. Call admin.', thread_ts=body['container']['message_ts'])

        elif action == ActionValue.Delete.name:
            logging.info('Action: Delete')

            entry = getEntry(entryId)

            if entry['status'] == 'trash':
                logging.warning('Entry ' + entryId + ' has already been deleted. No action will be taken.')
                return

            logging.info('Sending delete command for entry ' + entryId + '.')
            success = trashGravityFormsEntry(entryId)
            if success:
                self.post_msg_to_channel(text='Workout sent to trash by ' + user + '.', thread_ts=body['container']['message_ts'])
                logging.info('Entry deleted, action logged to Slack thread.')
            else:
                self.post_msg_to_channel(text='Workout deletion failed! ' + user + ' tried to send it to trash, the system failed. Call admin.', thread_ts=body['container']['message_ts'])

            deleteEntryId = actionValuePieces[2]
            deleteEntry = getEntry(deleteEntryId)
            deleteEntry['is_approved'] = "1"
            deleteEntry['is_read'] = "1"
            logging.info('Marking delete request entry ' + deleteEntryId + ' as read and approved.')
            updateEntry(deleteEntryId, deleteEntry)

        elif action == ActionValue.RejectDelete.name:
            logging.info('Action: Reject Delete')

            logging.info('Sending delete command for delete request entry ' + entryId + '.')
            success = trashGravityFormsEntry(entryId)
            if success:
                self.post_msg_to_channel(text='Workout will not be sent to trash, according to ' + user + '.', thread_ts=body['container']['message_ts'])
                logging.info('Delete request entry sent to trash, action logged to Slack thread.')
            else:
                self.post_msg_to_channel(text='Workout delete rejection failed! ' + user + ' tried to not send it to trash, the system failed. Call admin.', thread_ts=body['container']['message_ts'])

        else:
            logging.error('A Slack Action was received with an action value that is not handled: ' + actionValue)

        logging.info('Done handling Slack Action.')

    def post_msg_to_channel(self, text: str, blocks: list|None = None, thread_ts: str|None = None, unfurl: bool = False, channel: str = None) -> None:
        if channel is None:
            channel = self.MAP_CHANNEL_ID

        self.client.chat_postMessage(channel=channel, text=text, blocks=blocks, thread_ts=thread_ts, unfurl_links=unfurl, unfurl_media=unfurl))
        logging.info('Posted request to Slack. Done handling.')

    def build_delete_message(self, body: dict) -> list:
        message = []

        message.append(self._get_block_header('Map Request: Delete'))
        message.append(self._get_block_section('*Region:* ' + body['7'] + '\n*Workout Name:* ' + body['1'] + '\n\n*Reason:* ' + body['5'] + '\n\n*Submitter:* ' + body['4'] + '\n*Submitter Email:* ' + body['3']))
        message.append(self._get_block_section('Helpful Links: <' + os.getenv('GRAVITY_FORMS_BASE_URL') + '/wp-admin/admin.php?page=gf_entries&view=entry&lid=' + body['6'] + '&id=' + os.getenv('GRAVITY_FORM_WORKOUT_FORM_ID') + '|AO Entry>'))

        messageActions = self._get_block_actions()
        messageActions = self._get_block_actions_button(messageActions, 'Delete (trash)', ButtonStyle.danger, ActionValue.Delete.name + '_' + body['6'] + '_' + body['id'], True) # Button value includes workout entry followed by delete entry
        messageActions = self._get_block_actions_button(messageActions, 'Reject Delete Request', ButtonStyle.default, ActionValue.RejectDelete.name + '_' + body['id'])
        message.append(messageActions)

        return message

    def build_new_or_update_msg(self, body: dict) -> list:
        message = []

        submissionType = self._is_new_or_update(body)

        message.append(self._get_block_header('Map Request: ' + submissionType))
        message.append(self._get_block_section('*Region:* ' + body['21'] + '\n*Workout Name:* ' + body['2'] + '\n\n*Street 1:* ' + body['1.1'] + '\n*Street 2:* ' + body['1.2'] + '\n*City:* ' + body['1.3'] + '\n*State:* ' + body['1.4'] + '\n*ZIP Code:* ' + body['1.5'] + '\n*Country:* ' + body['1.6'] + '\n\n*Latitude:* ' + body['13'] + '\n*Longitude:* ' + body['12'] + '\n_Single quotes have been added to help see white space._\nAddress at Lat/Long: ' + 'Insert address here' + '\n\n*Weekday:* ' + body['14'] + '\n*Time:* ' + body['4'] + '\n*Type:* ' + body['5'] + '\n\n*Region Website:* ' + body['17'] + '\n*Region Logo:* ' + body['16'] + '\n\n*Notes:* ' + body['15'] + '\n\n*Submitter:* ' + body['18'] + '\n*Submitter Email:* ' + body['19'] + '\n*Original Submission (UTC):* ' + body['date_created']))
        message.append(self._get_block_section('Helpful Links: <' + os.getenv('GRAVITY_FORMS_BASE_URL') + '/wp-admin/admin.php?page=gf_entries&filter=gv_unapproved&id=' + body['form_id'] + '|All Unapproved Requests>, <' + os.getenv('GRAVITY_FORMS_BASE_URL') + '/wp-admin/admin.php?page=gf_entries&view=entry&id=' + body['form_id'] + '&lid=' + body['id'] + '|This Request>, <https://www.google.com/maps|Distance between address and lat/long>'))

        messageActions = self._get_block_actions()
        messageActions = self._get_block_actions_button(messageActions, 'Approve', ButtonStyle.primary, ActionValue.Approve.name + '_' + body['id'])
        message.append(messageActions)

        return message

    def _is_new_or_update(self, entry: dict) -> str:
        if entry['date_created'] == entry['date_updated']:
            return 'New'
        else:
            return 'Update'

    def _get_block_header(self, message: str) -> dict:
        # _ in front of a method usually i think means it's a private class that only will be called from within this class
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": message
            }
        }

    def _get_block_context(self, message: str) -> dict:
        return {
            "type": "context",
            "elements": [
                {
                    "type": "plain_text",
                    "text": message
                }
            ]
        }

    def _get_block_section(self, message: str) -> dict:
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message
            }
        }

    def _get_block_actions(self) -> dict:
        return {
            "type": "actions",
            "elements": []
        }

    def _get_block_actions_button(self, actionBlock: dict, buttonText: str, buttonStyle: ButtonStyle, buttonValue: str, addConfirmation: bool = False) -> dict:
        button =  {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": buttonText
            },
            "value": buttonValue
        }

        if buttonStyle != ButtonStyle.default:
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
