import logging
import os

from Functions.Shared import (
    buildNewOrUpdateMessage,
    buildDeleteMessage,
    postMessageToMapChannel
)

def handleGravityFormsSubmission(body: dict):
    logging.info('Handling Gravity Forms Workout.')
    logging.debug(body)

    if 'form_id' not in body:
        logging.error('Not a proper Gravity Forms payload. Payload does not include "form_id", which represents the form ID, and is required. Will not process')
        return
    
    if body['form_id'] != os.getenv('GRAVITY_FORM_WORKOUT_FORM_ID'):
        logging.error('Form ID submitted to the /webhooks/workout endpoint (' + body['form_id'] + ' does not match configured form ID (' + os.getenv('GRAVITY_FORM_WORKOUT_FORM_ID') + '). Will not process.')
        return

    blocks = buildNewOrUpdateMessage(body)
    region = body['21']
    
    postMessageToMapChannel('Map Request from ' + region, blocks)
    logging.info('Posted request to Slack. Done handling.')

def handleGravityFormsDelete(body: dict):
    logging.info('Handling Gravity Forms Workout Delete.')
    logging.debug(body)

    if 'form_id' not in body:
        logging.error('Not a proper Gravity Forms payload. Payload does not include "form_id", which represents the form ID, and is required. Will not process')
        return
    
    if body['form_id'] != os.getenv('GRAVITY_FORM_DELETE_FORM_ID'):
        logging.error('Form ID submitted to the /webhooks/workoutdelete endpoint (' + body['form_id'] + ' does not match configured form ID (' + os.getenv('GRAVITY_FORM_DELETE_FORM_ID') + '). Will not process.')
        return

    blocks = buildDeleteMessage(body)
    region = body['7']
    
    postMessageToMapChannel('Map Delete Request from ' + region, blocks)
    logging.info('Posted request to Slack. Done handling.')