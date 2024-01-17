import os
from slack_sdk import WebClient
import requests
import smtplib
from email.message import EmailMessage



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