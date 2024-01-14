from enum import Enum
import os
from slack_sdk import WebClient
import requests
import smtplib
from email.message import EmailMessage

# Slack
def GetBlockHeader(message: str) -> dict:
    return {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": message
        }
    }

def GetBlockContext(message: str) -> dict:
    return {
        "type": "context",
        "elements": [
            {
                "type": "plain_text",
                "text": message
            }
        ]
    }

def GetBlockSection(message: str) -> dict:
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": message
        }
    }

def GetBlockActions() -> dict:
    return {
        "type": "actions",
        "elements": []
    }

class ButtonStyle(Enum):
    """Changes the color of the button. Default is gray, Primary is green, Danger is red."""
    default = 0
    primary = 1
    danger = 2

def GetBlockActionsButton(actionBlock: dict, buttonText: str, buttonStyle: ButtonStyle, buttonValue: str, addConfirmation: bool = False) -> dict:
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

ActionValue = Enum('ActionValue', ['Approve', 'Delete', 'RejectDelete'])

def isNewOrUpdate(entry: dict) -> str:
    if entry['date_created'] == entry['date_updated']:
        return 'New'
    else:
        return 'Update'

def buildNewOrUpdateMessage(body: dict) -> list:
    message = []
    
    submissionType = isNewOrUpdate(body)

    message.append(GetBlockHeader('Map Request: ' + submissionType))
    message.append(GetBlockSection('*Region:* ' + body['21'] + '\n*Workout Name:* ' + body['2'] + '\n\n*Street 1:* ' + body['1.1'] + '\n*Street 2:* ' + body['1.2'] + '\n*City:* ' + body['1.3'] + '\n*State:* ' + body['1.4'] + '\n*ZIP Code:* ' + body['1.5'] + '\n*Country:* ' + body['1.6'] + '\n\n*Latitude:* ' + body['13'] + '\n*Longitude:* ' + body['12'] + '\n_Single quotes have been added to help see white space._\nAddress at Lat/Long: ' + 'Insert address here' + '\n\n*Weekday:* ' + body['14'] + '\n*Time:* ' + body['4'] + '\n*Type:* ' + body['5'] + '\n\n*Region Website:* ' + body['17'] + '\n*Region Logo:* ' + body['16'] + '\n\n*Notes:* ' + body['15'] + '\n\n*Submitter:* ' + body['18'] + '\n*Submitter Email:* ' + body['19'] + '\n*Original Submission (UTC):* ' + body['date_created']))
    message.append(GetBlockSection('Helpful Links: <' + os.getenv('GRAVITY_FORMS_BASE_URL') + '/wp-admin/admin.php?page=gf_entries&filter=gv_unapproved&id=' + body['form_id'] + '|All Unapproved Requests>, <' + os.getenv('GRAVITY_FORMS_BASE_URL') + '/wp-admin/admin.php?page=gf_entries&view=entry&id=' + body['form_id'] + '&lid=' + body['id'] + '|This Request>, <https://www.google.com/maps|Distance between address and lat/long>'))

    messageActions = GetBlockActions()
    messageActions = GetBlockActionsButton(messageActions, 'Approve', ButtonStyle.primary, ActionValue.Approve.name + '_' + body['id'])
    message.append(messageActions)

    return message

def buildDeleteMessage(body: dict) -> list:
    message = []

    message.append(GetBlockHeader('Map Request: Delete'))
    message.append(GetBlockSection('*Region:* ' + body['7'] + '\n*Workout Name:* ' + body['1'] + '\n\n*Reason:* ' + body['5'] + '\n\n*Submitter:* ' + body['4'] + '\n*Submitter Email:* ' + body['3']))
    message.append(GetBlockSection('Helpful Links: <' + os.getenv('GRAVITY_FORMS_BASE_URL') + '/wp-admin/admin.php?page=gf_entries&view=entry&lid=' + body['6'] + '&id=' + os.getenv('GRAVITY_FORM_WORKOUT_FORM_ID') + '|AO Entry>'))

    messageActions = GetBlockActions()
    messageActions = GetBlockActionsButton(messageActions, 'Delete (trash)', ButtonStyle.danger, ActionValue.Delete.name + '_' + body['6'] + '_' + body['id'], True) # Button value includes workout entry followed by delete entry
    messageActions = GetBlockActionsButton(messageActions, 'Reject Delete Request', ButtonStyle.default, ActionValue.RejectDelete.name + '_' + body['id'])
    message.append(messageActions)

    return message

def getSlackDisplayName(userId: str) -> str:
    client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
    user = client.users_profile_get(user=userId)
    return user['profile']['display_name_normalized']

def postMessageToMapChannel(text: str, blocks: list|None = None, thread_ts: str|None = None, unfurl: bool = False) -> None:
    client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))

    client.chat_postMessage(channel=os.getenv('SLACK_MAP_CHANNEL_ID'), text=text, blocks=blocks, thread_ts=thread_ts, unfurl_links=unfurl, unfurl_media=unfurl)

# Gravity Forms
def getEntry(entryId: str) -> dict:
    response = requests.get(os.getenv('GRAVITY_FORMS_BASE_URL') + '/wp-json/gf/v2/entries/' + entryId, auth=(os.getenv('GRAVITY_FORM_KEY'), os.getenv('GRAVITY_FORM_SECRET')))
    response.encoding = 'utf-8-sig'
    entry = response.json()
    
    return entry

def updateEntry(entryId: str, entry: dict) -> bool:
    """Updates indicated entry with the json provided. Will return True if response from Gravity Forms is 200."""
    
    response = requests.put(os.getenv('GRAVITY_FORMS_BASE_URL') + '/wp-json/gf/v2/entries/' + entryId, json=entry, auth=(os.getenv('GRAVITY_FORM_KEY'), os.getenv('GRAVITY_FORM_SECRET')))

    return response.status_code == 200

def trashGravityFormsEntry(entryId: str) -> bool:
    
    response = requests.delete(os.getenv('GRAVITY_FORMS_BASE_URL') + '/wp-json/gf/v2/entries/' + entryId, auth=(os.getenv('GRAVITY_FORM_KEY'), os.getenv('GRAVITY_FORM_SECRET')))

    return response.status_code == 200

def getUnapprovedCount(formId: str) -> int:
    param = {"search": '{"field_filters": [{"key":"is_approved","value":3,"operator":"="}]}'}
    response = requests.get(os.getenv('GRAVITY_FORMS_BASE_URL') + '/wp-json/gf/v2/forms/' + formId + '/entries', params=param, auth=(os.getenv('GRAVITY_FORM_KEY'), os.getenv('GRAVITY_FORM_SECRET')))
    response.encoding = 'utf-8-sig'
    body = response.json()

    return int(body['total_count'])

# Email
def sendEmail(subject: str, toEmails: list, body: str) -> None:
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()
    smtp.login('map.admin@f3nation.com', 'Wxa74L9Bcp^B^pFe')

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = 'maps-admins@f3nation.com'
    message['To'] = ', '.join(toEmails)
    message.set_content(body, subtype='html')

    smtp.send_message(message)