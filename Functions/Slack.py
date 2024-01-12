import logging
from Functions.Shared import (
    getEntry,
    updateEntry,
    postMessageToMapChannel,
    getSlackDisplayName,
    deleteGravityFormsEntry,
    ActionValue
)

def handleSlackAction(body: dict):
    logging.debug(body)

    actionValue = body['actions'][0]['value']
    logging.debug('Action value: ' + body['actions'][0]['value'])
    actionValuePieces = str.split(actionValue, '_')
    action = actionValuePieces[0]
    entryId = actionValuePieces[1]
    user = getSlackDisplayName(body['user']['id'])

    if action == ActionValue.Approve.name:
        entry = getEntry(entryId)
        entry['is_approved'] = "1"
        
        success = updateEntry(entryId, entry)
        if success:
            postMessageToMapChannel(text='Map Request approved by ' + user + '.', thread_ts=body['container']['message_ts'])
        else:
            postMessageToMapChannel(text='Map Request Approval Failed! ' + user + ' tried to approve it, the system failed. Call admin.', thread_ts=body['container']['message_ts'])
    elif action == ActionValue.Delete.name:
        success = deleteGravityFormsEntry(entryId)
        if success:
            postMessageToMapChannel(text='Workout sent to trash by ' + user + '.', thread_ts=body['container']['message_ts'])
        else:
            postMessageToMapChannel(text='Workout deletion failed! ' + user + ' tried to send it to trash, the system failed. Call admin.', thread_ts=body['container']['message_ts'])
    
        entry = getEntry(actionValuePieces[2]) # ID of the Delete request
        entry['is_approved'] = "1"
        updateEntry(entryId, entry)

    elif action == ActionValue.RejectDelete.name:
        success = deleteGravityFormsEntry(entryId)
        if success:
            postMessageToMapChannel(text='Workout will not be sent to trash, according to ' + user + '.', thread_ts=body['container']['message_ts'])
        else:
            postMessageToMapChannel(text='Workout delete rejection failed! ' + user + ' tried to not send it to trash, the system failed. Call admin.', thread_ts=body['container']['message_ts'])

    else:
        logging.error('A Slack Action was received with an action value that is not handled: ' + actionValue)