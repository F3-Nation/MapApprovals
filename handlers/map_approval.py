import logging
from functions.slack import Slack, Action_Value, Button_Style
from functions.gravity_forms import GravityForms
from functions.shared import (
    send_email
)

class MapApprovalHandler:
    
    def __init__(self) -> None:
        self.gravity_forms = GravityForms()
        self.slack = Slack()

    def handle_gravity_forms_submission(self, entry: dict):
        logging.info('Handling Gravity Forms Workout.')
        logging.debug(entry)

        if 'form_id' not in entry:
            logging.error('Not a proper Gravity Forms payload. Payload does not include "form_id", which represents the form ID, and is required. Will not process')
            return

        if entry['form_id'] != self.gravity_forms.FORM_ID_WORKOUT:
            logging.error('Form ID submitted to the /webhooks/workout endpoint (' + entry['form_id'] + ' does not match configured form ID (' + self.gravity_forms.FORM_ID_WORKOUT + '). Will not process.')
            return

        submissionType = GravityForms.is_new_or_update(entry)
        region = entry['21']
        workout_name = entry['2']
        street_1 = entry['1.1']
        street_2 = entry['1.2']
        city = entry['1.3']
        state = entry['1.4']
        zip_code = entry['1.5']
        country = entry['1.6']
        latitude = entry['13']
        longitude = entry['12']
        weekday = entry['14']
        time = entry['4']
        workout_type = entry['5']
        website = entry['17']
        logo = entry['16']
        notes = entry['15']
        submitter_name = entry['18']
        submitter_email = entry['19']

        blocks = Slack.start_blocks()
        blocks.append(Slack.get_block_header('Map Request: ' + submissionType))
        blocks.append(Slack.get_block_section('*Region:* ' + region + '\n*Workout Name:* ' + workout_name + '\n\n*Street 1:* ' + street_1 + '\n*Street 2:* ' + street_2 + '\n*City:* ' + city + '\n*State:* ' + state + '\n*ZIP Code:* ' + zip_code + '\n*Country:* ' + country + '\n\n*Latitude:* ' + latitude + '\n*Longitude:* ' + longitude + '\n_Single quotes have been added to help see white space._\nAddress at Lat/Long: ' + 'Insert address here' + '\n\n*Weekday:* ' + weekday + '\n*Time:* ' + time + '\n*Type:* ' + workout_type + '\n\n*Region Website:* ' + website + '\n*Region Logo:* ' + logo + '\n\n*Notes:* ' + notes + '\n\n*Submitter:* ' + submitter_name + '\n*Submitter Email:* ' + submitter_email + '\n*Original Submission (UTC):* ' + entry['date_created']))
        blocks.append(Slack.get_block_section('Helpful Links: <' + self.gravity_forms.BASE_URL + '/wp-admin/admin.php?page=gf_entries&filter=gv_unapproved&id=' + entry['form_id'] + '|All Unapproved Requests>, <' + self.gravity_forms.BASE_URL + '/wp-admin/admin.php?page=gf_entries&view=entry&id=' + entry['form_id'] + '&lid=' + entry['id'] + '|This Request>, <https://www.google.com/maps|Distance between address and lat/long>'))

        blocks.append(Slack.get_divider())

        blockActions = Slack.get_block_actions()
        blockActions = Slack.get_block_actions_button(blockActions, 'Approve', Button_Style.primary, Action_Value.Approve.name + '_' + entry['id'])
        blocks.append(blockActions)

        self.slack.post_msg_to_channel('Map Request from ' + region, blocks)
    
    
    def handle_gravity_forms_delete(self, entry: dict):
        logging.info('Handling Gravity Forms Workout Delete.')
        logging.debug(entry)

        if 'form_id' not in entry:
            logging.error('Not a proper Gravity Forms payload. Payload does not include "form_id", which represents the form ID, and is required. Will not process')
            return

        if entry['form_id'] != self.gravity_forms.FORM_ID_WORKOUT_DELETE:
            logging.error('Form ID submitted to the /webhooks/workoutdelete endpoint (' + entry['form_id'] + ' does not match configured form ID (' + self.gravity_forms.FORM_ID_WORKOUT_DELETE + '). Will not process.')
            return

        region = entry['7']
        workout_name = entry['1']
        reason = entry['5']
        submitter_name = entry['4']
        submitter_email = entry['3']
        workout_to_delete = entry['6']

        blocks = Slack.start_blocks()
        blocks.append(Slack.get_block_header('Map Request: Delete'))
        blocks.append(Slack.get_block_section('*Region:* ' + region + '\n*Workout Name:* ' + workout_name + '\n\n*Reason:* ' + reason + '\n\n*Submitter:* ' + submitter_name + '\n*Submitter Email:* ' + submitter_email))
        blocks.append(Slack.get_block_section('Helpful Links: <' + self.gravity_forms.BASE_URL + '/wp-admin/admin.php?page=gf_entries&view=entry&lid=' + workout_to_delete + '&id=' + self.gravity_forms.FORM_ID_WORKOUT + '|AO Entry>'))

        blocks.append(Slack.get_divider())
        
        blockActions = Slack.get_block_actions()
        blockActions = Slack.get_block_actions_button(blockActions, 'Delete (trash)', Button_Style.danger, Action_Value.Delete.name + '_' + workout_to_delete + '_' + entry['id'], True) # Button value includes workout entry followed by delete entry
        blockActions = Slack.get_block_actions_button(blockActions, 'Reject Delete Request', Button_Style.default, Action_Value.RejectDelete.name + '_' + entry['id'])
        blocks.append(blockActions)

        self.slack.post_msg_to_channel('Map Delete Request from ' + region, blocks)

    
    def handle_slack_action(self, body: dict):
        logging.debug(body)
        logging.info('Handling Slack Action.')

        actionValue = body['actions'][0]['value']
        logging.debug('Action value: ' + body['actions'][0]['value'])
        action_value_pieces = str.split(actionValue, '_')

        if len(action_value_pieces) < 2:
            logging.error('Action value (' + actionValue + ') is not valid. Must be at least 2 parts (separated by _), Action, followed by an Entry ID. There may be additional parts, but at least 2 are required. Will not process.')
            return

        action = action_value_pieces[0]
        entryId = action_value_pieces[1]
        user = self.slack.get_display_name(body['user']['id'])

        if action == Action_Value.Approve.name:
            logging.info('Action: Approve')
            entry = self.gravity_forms.get_entry(entryId) # Get latest version
            entry['is_approved'] = "1"
            entry['is_read'] = "1"

            submissionType = GravityForms.is_new_or_update(entry)
            
            logging.info('For entry ' + entryId + ', set is_approved and is_read to 1. Updating entry.')
            success = self.gravity_forms.update_entry(entryId, entry)
            if success:
                statusBlock = Slack.get_block_section('Request approved by <@' + body['user']['id'] + '> at ' + Slack.convert_ts_to_utc(body['actions'][0]['action_ts']))
                blocks = Slack.replace_buttons(blocks=body['message']['blocks'], newBlock=statusBlock)
                self.slack.replace_msg(interactivePayload=body, blocks=blocks)
                send_email('Map Request Approved', [entry['19']], '<div style="display: none; max-height: 0px; overflow: hidden;">' + submissionType + ' -> ' + entry['2'] + ' @ ' + entry['21'] + '</div><div style="display: none; max-height: 0px; overflow: hidden;">&#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy;</div><p>Your map request has been approved and should show up on <a href="https://map.f3nation.com">the map</a> within the hour. If you see a mistake, use this <a href="' + self.gravity_forms.BASE_URL + '/map-changes">link</a> to submit a correction. Reply to this email with any other issues.</p><table border="1" style="border-collapse:collapse" cellpadding="5"><tr><td><b>Region</b></td><td>' + entry['21'] + '</td></tr><tr><td><b>Workout Name</b></td><td>' + entry['2'] + '</td></tr><tr><td><b>Street 1</b></td><td>' + entry['1.1'] + '</td></tr><tr><td><b>Street 2</b></td><td>' + entry['1.2'] + '</td></tr><tr><td><b>City</b></td><td>' + entry['1.3'] + '</td></tr><tr><td><b>State</b></td><td>' + entry['1.4'] + '</td></tr><tr><td><b>ZIP Code</b></td><td>' + entry['1.5'] + '</td></tr><tr><td><b>United States</b></td><td>' + entry['1.6'] + '</td></tr><tr><td><b>Latitude</b></td><td>' + entry['13'] + '</td></tr><tr><td><b>Longitude</b></td><td>' + entry['12'] + '</td></tr><tr><td><b>Weekday</b></td><td>' + entry['14'] + '</td></tr><tr><td><b>Time</b></td><td>' + entry['4'] + '</td></tr><tr><td><b>Type</b></td><td>' + entry['5'] + '</td></tr><tr><td><b>Region Website</b></td><td>' + entry['17'] + '</td></tr><tr><td><b>Region Logo</b></td><td>' + entry['16'] + '</td></tr><tr><td><b>Notes</b></td><td>' + entry['15'] + '</td></tr><tr><td><b>Submitter</b></td><td>' + entry['18'] + '</td></tr><tr><td><b>Submitter Email</b></td><td>' + entry['19'] + '</td></tr><tr><td><b>Request Created</b></td><td>' + entry['date_created'] + ' UTC</td></tr><tr><td><b>Request Updated</b></td><td>' + entry['date_updated'] + ' UTC</td></tr></table>')
                self.slack.post_msg_to_channel(text='Map Request approved by ' + user + '.', thread_ts=body['container']['message_ts'])
                logging.info('Entry updated, action logged to Slack thread, requestor emailed.')
            else:
                logging.error('Could not approve entry ' + entryId)
                self.slack.post_msg_to_channel(text='Map Request Approval Failed! ' + user + ' tried to approve it, the system failed. Call admin.', thread_ts=body['container']['message_ts'])

        elif action == Action_Value.Delete.name:
            logging.info('Action: Delete')

            entry = self.gravity_forms.get_entry(entryId)

            if entry['status'] == 'trash':
                logging.warning('Entry ' + entryId + ' has already been deleted. No action will be taken.')
                return

            logging.info('Sending delete command for entry ' + entryId + '.')
            success = self.gravity_forms.trash_entry(entryId)
            if success:
                self.slack.post_msg_to_channel(text='Workout sent to trash by ' + user + '.', thread_ts=body['container']['message_ts'])
                logging.info('Entry deleted, action logged to Slack thread.')
            else:
                self.slack.post_msg_to_channel(text='Workout deletion failed! ' + user + ' tried to send it to trash, the system failed. Call admin.', thread_ts=body['container']['message_ts'])

            deleteEntryId = action_value_pieces[2]
            deleteEntry = self.gravity_forms.get_entry(deleteEntryId)
            deleteEntry['is_approved'] = "1"
            deleteEntry['is_read'] = "1"
            logging.info('Marking delete request entry ' + deleteEntryId + ' as read and approved.')
            self.gravity_forms.update_entry(deleteEntryId, deleteEntry)

        elif action == Action_Value.RejectDelete.name:
            logging.info('Action: Reject Delete')

            logging.info('Sending delete command for delete request entry ' + entryId + '.')
            success = self.gravity_forms.trash_entry(entryId)
            if success:
                self.slack.post_msg_to_channel(text='Workout will not be sent to trash, according to ' + user + '.', thread_ts=body['container']['message_ts'])
                logging.info('Delete request entry sent to trash, action logged to Slack thread.')
            else:
                self.slack.post_msg_to_channel(text='Workout delete rejection failed! ' + user + ' tried to not send it to trash, the system failed. Call admin.', thread_ts=body['container']['message_ts'])

        else:
            logging.error('A Slack Action was received with an action value that is not handled: ' + actionValue)

        logging.info('Done handling Slack Action.')
    
    def handleCheckUnapprovedTrigger(self) -> None:
        logging.info('Handline Check Unapproved.')
        unapprovedUpdateCount = self.gravity_forms.get_unapproved_count(self.gravity_forms.FORM_ID_WORKOUT)
        unapprovedDeleteCount = self.gravity_forms.get_unapproved_count(self.gravity_forms.FORM_ID_WORKOUT_DELETE)

        if unapprovedUpdateCount == 0 & unapprovedDeleteCount == 0:
            logging.info('No unapproved.')
            return
        
        message = []
        if unapprovedUpdateCount > 0:
            message.append(str(unapprovedUpdateCount) + ' updates')
        if unapprovedDeleteCount > 0:
            message.append(str(unapprovedDeleteCount) + ' deletes')
        
        self.slack.post_msg_to_channel(text='<!channel>, there are unapproved requests: ' + ', '.join(message) + '. <' + self.gravity_forms.BASE_URL + '/wp-admin/admin.php?page=gf_entries&filter=gv_unapproved&id=' + self.gravity_forms.FORM_ID_WORKOUT + '|Link>')
        logging.info('Sent unapproved counts to Slack. Done handling.')
