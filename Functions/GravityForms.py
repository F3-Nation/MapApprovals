import logging
import os

from Functions.Shared import (
    buildNewOrUpdateMessage,
    buildDeleteMessage,
    postMessageToMapChannel
)

def handleGravityFormsSubmission(body: dict):
    logging.debug(body)

    if 'form_id' not in body:
        logging.error('Not a proper Gravity Forms payload. Payload does not include "form_id", which represents the form ID, and is required.')
        return
    logging.debug(os.getenv('GRAVITY_FORM_WORKOUT_FORM_ID'))

    formId = body['form_id']
    if formId == os.getenv('GRAVITY_FORM_WORKOUT_FORM_ID'):
        region = body['21']
        blocks = buildNewOrUpdateMessage(body)
    elif formId == os.getenv('GRAVITY_FORM_DELETE_FORM_ID'):
        region = body['7']
        blocks = buildDeleteMessage(body)
    else:
        logging.warning("Gravity Form submission received with Form ID of " + formId + ". This is not one of the configured Form IDs. If there is a new Form ID, update the input variables with the new ID.")
        return
    
    postMessageToMapChannel('Map Request from ' + region, blocks)

