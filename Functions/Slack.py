import logging
import os
from Functions.Shared import (
    getEntry,
    updateEntry,
    postMessageToMapChannel,
    getSlackDisplayName,
    trashGravityFormsEntry,
    ActionValue,
    sendEmail,
    isNewOrUpdate
)

def handleSlackAction(body: dict):
    logging.debug(body)
    logging.info('Handling Slack Action.')

    actionValue = body['actions'][0]['value']
    logging.debug('Action value: ' + body['actions'][0]['value'])
    actionValuePieces = str.split(actionValue, '_')
    action = actionValuePieces[0]
    entryId = actionValuePieces[1]
    user = getSlackDisplayName(body['user']['id'])

    if action == ActionValue.Approve.name:
        logging.info('Action: Approve')
        entry = getEntry(entryId)
        entry['is_approved'] = "1"
        entry['is_read'] ="1"

        submissionType = isNewOrUpdate(entry)

        logging.info('For entry ' + entryId + ', set is_approved and is_read to 1. Updating entry.')
        success = updateEntry(entryId, entry)
        if success:
            postMessageToMapChannel(text='Map Request approved by ' + user + '.', thread_ts=body['container']['message_ts'])
            sendEmail('Map Request Approved', [entry['19']], '<div style="display: none; max-height: 0px; overflow: hidden;">' + submissionType + ' -> ' + entry['2'] + ' @ ' + entry['21'] + '</div><div style="display: none; max-height: 0px; overflow: hidden;">&#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy;</div><p>Your map request has been approved and should show up on <a href="https://map.f3nation.com">the map</a> within the hour. If you see a mistake, use this <a href="' + os.getenv('GRAVITY_FORMS_BASE_URL') + '/wp-admin/admin.php?page=gf_entries&view=entry&screen_mode=edit&id=' + os.getenv('GRAVITY_FORM_WORKOUT_FORM_ID') + '&lid=' + entry['id'] + '">link</a> to submit a correction. Reply to this email with any other issues.</p><table border="1" style="border-collapse:collapse" cellpadding="5"><tr><td><b>Region</b></td><td>' + entry['21'] + '</td></tr><tr><td><b>Workout Name</b></td><td>' + entry['2'] + '</td></tr><tr><td><b>Street 1</b></td><td>' + entry['1.1'] + '</td></tr><tr><td><b>Street 2</b></td><td>' + entry['1.2'] + '</td></tr><tr><td><b>City</b></td><td>' + entry['1.3'] + '</td></tr><tr><td><b>State</b></td><td>' + entry['1.4'] + '</td></tr><tr><td><b>ZIP Code</b></td><td>' + entry['1.5'] + '</td></tr><tr><td><b>United States</b></td><td>' + entry['1.6'] + '</td></tr><tr><td><b>Latitude</b></td><td>' + entry['13'] + '</td></tr><tr><td><b>Longitude</b></td><td>' + entry['12'] + '</td></tr><tr><td><b>Weekday</b></td><td>' + entry['14'] + '</td></tr><tr><td><b>Time</b></td><td>' + entry['4'] + '</td></tr><tr><td><b>Type</b></td><td>' + entry['5'] + '</td></tr><tr><td><b>Region Website</b></td><td>' + entry['17'] + '</td></tr><tr><td><b>Region Logo</b></td><td>' + entry['16'] + '</td></tr><tr><td><b>Notes</b></td><td>' + entry['15'] + '</td></tr><tr><td><b>Submitter</b></td><td>' + entry['18'] + '</td></tr><tr><td><b>Submitter Email</b></td><td>' + entry['19'] + '</td></tr><tr><td><b>Request Created</b></td><td>' + entry['date_created'] + ' UTC</td></tr><tr><td><b>Request Updated</b></td><td>' + entry['date_updated'] + ' UTC</td></tr></table>')
            logging.info('Entry updated, action logged to Slack thread, requestor emailed.')
        else:
            logging.error('Could not approve entry ' + entryId)
            postMessageToMapChannel(text='Map Request Approval Failed! ' + user + ' tried to approve it, the system failed. Call admin.', thread_ts=body['container']['message_ts'])
    
    elif action == ActionValue.Delete.name:
        logging.info('Action: Delete')
        
        entry = getEntry(entryId)

        if entry['status'] == 'trash':
            logging.warning('Entry ' + entryId + ' has already been deleted. No action will be taken.')
            return

        logging.info('Sending delete command for entry ' + entryId + '.')
        success = trashGravityFormsEntry(entryId)
        if success:
            postMessageToMapChannel(text='Workout sent to trash by ' + user + '.', thread_ts=body['container']['message_ts'])
            logging.info('Entry deleted, action logged to Slack thread.')
        else:
            postMessageToMapChannel(text='Workout deletion failed! ' + user + ' tried to send it to trash, the system failed. Call admin.', thread_ts=body['container']['message_ts'])
    
        deleteEntryId = actionValuePieces[2]
        deleteEntry = getEntry(deleteEntryId)
        deleteEntry['is_approved'] = "1"
        deleteEntry['is_read'] ="1"
        logging.info('Marking delete request entry ' + deleteEntryId + ' as read and approved.')
        updateEntry(deleteEntryId, deleteEntry)

    elif action == ActionValue.RejectDelete.name:
        logging.info('Action: Reject Delete')

        logging.info('Sending delete command for delete request entry ' + entryId + '.')
        success = trashGravityFormsEntry(entryId)
        if success:
            postMessageToMapChannel(text='Workout will not be sent to trash, according to ' + user + '.', thread_ts=body['container']['message_ts'])
            logging.info('Delete request entry sent to trash, action logged to Slack thread.')
        else:
            postMessageToMapChannel(text='Workout delete rejection failed! ' + user + ' tried to not send it to trash, the system failed. Call admin.', thread_ts=body['container']['message_ts'])

    else:
        logging.error('A Slack Action was received with an action value that is not handled: ' + actionValue)

    logging.info('Done handling Slack Action.')