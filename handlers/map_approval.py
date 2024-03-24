import logging
import os
from services.slack import Slack, Action_Value, Button_Style, Views
from services.gravity_forms import GravityForms
from services.smtp import SMTP
from services.map import Map

class MapApprovalHandler:
    _ALERT_DISTANCE_FEET = float(os.getenv('ALERT_DISTANCE_FEET'))
    
    def __init__(self) -> None:
        self.gravity_forms = GravityForms()
        self.slack = Slack()
        self.smtp = SMTP()
        self.map = Map()

    def _build_workout_slack_blocks(self, entry: dict) -> list:
        
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
        date_created = GravityForms.convert_date_to_et(entry['date_created'])

        full_address = street_1 + ' ' + street_2 + ' ' + city + ' ' + state + ' ' + zip_code + ' ' + country
        address_at_lat_long = self.map.get_address_from_latlong(latitude=latitude, longitude=longitude)
        address_url = Map.get_address_url(full_address)
        lat_long_url = Map.get_address_url(latitude + ',' + longitude)
        direction_url = Map.get_directions_url(origin=full_address, destination=latitude + ',' + longitude)
        pin_to_address_distance = self.map.get_feet_between_address_and_latlong(address=full_address, latitude=latitude, longitude=longitude)
        if type(pin_to_address_distance) is int:
            pin_to_address_distance = '{0:,.0f}'.format(pin_to_address_distance) + ' ft'

        blocks = Slack.start_blocks()
        blocks.append(Slack.get_block_header('Map Request: ' + submissionType))
        blocks.append(Slack.get_block_section('*Region:* ' + region + '\n*Workout Name:* ' + workout_name + '\n\n*Street 1:* ' + street_1 + '\n*Street 2:* ' + street_2 + '\n*City:* ' + city + '\n*State:* ' + state + '\n*ZIP Code:* ' + zip_code + '\n*Country:* ' + country + '\n<' + address_url + '|Map It>\n\n*Latitude:* \'' + latitude + '\'\n*Longitude:* \'' + longitude + '\'\n<' + lat_long_url + '|Map It>\n\n*Address at Lat/Long:* ' + address_at_lat_long + '\n*Lat/Long to Address Distance:* ' + pin_to_address_distance + '\n\n*Weekday:* ' + weekday + '\n*Time:* ' + time + '\n*Type:* ' + workout_type + '\n\n*Region Website:* ' + website + '\n*Region Logo:* ' + logo + '\n\n*Notes:* ' + notes + '\n\n*Submitter:* ' + submitter_name + '\n*Submitter Email:* ' + submitter_email + '\n*Original Submission:* ' + date_created))
        blocks.append(Slack.get_block_section('Helpful Links: <' + self.gravity_forms.BASE_URL + '/wp-admin/admin.php?page=gf_entries&filter=gv_unapproved&id=' + entry['form_id'] + '|All Unapproved Requests>, <' + self.gravity_forms.BASE_URL + '/wp-admin/admin.php?page=gf_entries&view=entry&id=' + entry['form_id'] + '&lid=' + entry['id'] + '|This Request>, <' + direction_url + '|Directions from address to lat/long>'))

        blocks.append(Slack.get_divider())

        blockActions = Slack.get_block_actions()
        blockActions = Slack.get_block_actions_button(blockActions, 'Approve', Button_Style.primary, Action_Value.Approve.name + '_' + entry['id'])
        blockActions = Slack.get_block_actions_button(blockActions, 'Edit', Button_Style.default, Action_Value.Edit.name + '_' + entry['id'])
        blockActions = Slack.get_block_actions_button(blockActions, 'Refresh', Button_Style.default, Action_Value.Refresh.name + '_' + entry['id'])
        blockActions = Slack.get_block_actions_button(blockActions, 'Mark Complete', Button_Style.default, Action_Value.MarkComplete.name)
        blocks.append(blockActions)

        blocks.append(Slack.get_divider())

        return blocks
    
    
    def _build_edit_view_content(self, entry: dict) -> dict:
        
        workout_name = entry['2']
        street_1 = entry['1.1']
        street_2 = entry['1.2']
        city = entry['1.3']
        state = entry['1.4']
        zip_code = entry['1.5']
        latitude = entry['13']
        longitude = entry['12']
        website = entry['17']
        notes = entry['15']
        submitter_name = entry['18']
        submitter_email = entry['19']

        blocks = []
        blocks.append(Slack.get_block_section(message='Region, country, weekday, time, and workout type must be edited from Wordpress. Original post will be refreshed shortly after you submit edits.'))
        blocks.append(Slack.get_block_input(id='workout_name', label='Workout Name', initial_value = workout_name))
        blocks.append(Slack.get_block_input(id='street_1', label='Street 1', initial_value = street_1))
        blocks.append(Slack.get_block_input(id='street_2', label='Street 2', initial_value = street_2))
        blocks.append(Slack.get_block_input(id='city', label='City', initial_value = city))
        blocks.append(Slack.get_block_input(id='state', label='State', initial_value = state))
        blocks.append(Slack.get_block_input(id='zip_code', label='ZIP Code', initial_value = zip_code))
        blocks.append(Slack.get_block_input(id='latitude', label='Latitude', initial_value = latitude))
        blocks.append(Slack.get_block_input(id='longitude', label='Longitude', initial_value = longitude))
        blocks.append(Slack.get_block_input(id='website', label='Website', initial_value = website, multiline=True))
        blocks.append(Slack.get_block_input(id='notes', label='Notes', initial_value = notes, multiline=True))
        blocks.append(Slack.get_block_input(id='submitter_name', label='Submitter Name', initial_value = submitter_name))
        blocks.append(Slack.get_block_input(id='submitter_email', label='Submitter email', initial_value = submitter_email))

        return blocks
    

    def handle_gravity_forms_submission(self, entry: dict):
        logging.info('Handling Gravity Forms Workout.')
        logging.debug(entry)

        if 'form_id' not in entry:
            logging.error('Not a proper Gravity Forms payload. Payload does not include "form_id", which represents the form ID, and is required. Will not process')
            return

        if entry['form_id'] != self.gravity_forms.FORM_ID_WORKOUT:
            logging.error('Form ID submitted to the /webhooks/workout endpoint (' + entry['form_id'] + ' does not match configured form ID (' + self.gravity_forms.FORM_ID_WORKOUT + '). Will not process.')
            return

        blocks = self._build_workout_slack_blocks(entry=entry)
        region = entry['21']

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

        blocks.append(Slack.get_divider())

        self.slack.post_msg_to_channel('Map Delete Request from ' + region, blocks)

    
    def handle_slack_action(self, body: dict):
        logging.debug(body)
        logging.info('Handling Slack Action.')

        action_value = body['actions'][0]['value']
        logging.debug('Action value: ' + action_value)
        action_value_pieces = str.split(action_value, '_')
        action = action_value_pieces[0]
        user_id = body['user']['id']
        user_name = self.slack.get_display_name(user_id)

        if action == Action_Value.Approve.name:
            logging.info('Action: Approve')

            entryId = action_value_pieces[1]
            entry = self.gravity_forms.get_entry(entryId) # Get latest version
            entry['is_approved'] = "1"
            entry['is_read'] = "1"
            
            logging.info('For entry ' + entryId + ', setting is_approved and is_read to 1. Updating entry.')
            success = self.gravity_forms.update_entry(entryId, entry)
            if success:
                statusBlock = Slack.get_block_section('Request approved by <@' + body['user']['id'] + '> at ' + Slack.convert_ts_to_et(body['actions'][0]['action_ts']))
                blocks = Slack.replace_buttons(blocks=body['message']['blocks'], newBlock=statusBlock)
                self.slack.replace_msg(original_message=body['message'], ts=body['container']['message_ts'], blocks=blocks)
                
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
                date_created = GravityForms.convert_date_to_et(entry['date_created'])
                date_updated = GravityForms.convert_date_to_et(entry['date_updated'])

                full_address = street_1 + ' ' + street_2 + ' ' + city + ' ' + state + ' ' + zip_code + ' ' + country
                pin_to_address_distance = self.map.get_feet_between_address_and_latlong(address=full_address, latitude=latitude, longitude=longitude)
                if type(pin_to_address_distance) is int and pin_to_address_distance > self._ALERT_DISTANCE_FEET:
                    discrepency_warning = '<p/><div style="background-color: yellow;"><b><u>WARNING:</u></b> The distance between the address provided and the latitude/longitude provided is ' + '{0:,.0f}'.format(pin_to_address_distance) + ' feet. If you are ok with this, no action is needed. If you think they should be closer, please research the issue and submit necessary changes using the link above. If you need help getting this information accurate, please repl to this email.</div><p/>'
                else:
                    discrepency_warning = ''
                
                self.smtp.send_email('Map Request Approved', [submitter_email], '<div style="display: none; max-height: 0px; overflow: hidden;">' + submissionType + ' -> ' + workout_name + ' @ ' + region + '</div><div style="display: none; max-height: 0px; overflow: hidden;">&#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy;</div><p>Your map request has been approved and should show up on <a href="https://map.f3nation.com">the map</a> within the hour. If you see a mistake, use this <a href="' + self.gravity_forms.BASE_URL + '/map-changes">link</a> to submit a correction. Reply to this email with any other issues.</p>' + discrepency_warning + '<table border="1" style="border-collapse:collapse" cellpadding="5"><tr><td><b>Region</b></td><td>' + region + '</td></tr><tr><td><b>Workout Name</b></td><td>' + workout_name + '</td></tr><tr><td><b>Street 1</b></td><td>' + street_1 + '</td></tr><tr><td><b>Street 2</b></td><td>' + street_2 + '</td></tr><tr><td><b>City</b></td><td>' + city + '</td></tr><tr><td><b>State</b></td><td>' + state + '</td></tr><tr><td><b>ZIP Code</b></td><td>' + zip_code + '</td></tr><tr><td><b>United States</b></td><td>' + country + '</td></tr><tr><td><b>Latitude</b></td><td>' + latitude + '</td></tr><tr><td><b>Longitude</b></td><td>' + longitude + '</td></tr><tr><td><b>Weekday</b></td><td>' + weekday + '</td></tr><tr><td><b>Time</b></td><td>' + time + '</td></tr><tr><td><b>Type</b></td><td>' + workout_type + '</td></tr><tr><td><b>Region Website</b></td><td>' + website + '</td></tr><tr><td><b>Region Logo</b></td><td>' + logo + '</td></tr><tr><td><b>Notes</b></td><td>' + notes + '</td></tr><tr><td><b>Submitter</b></td><td>' + submitter_name + '</td></tr><tr><td><b>Submitter Email</b></td><td>' + submitter_email + '</td></tr><tr><td><b>Request Created</b></td><td>' + date_created + '</td></tr><tr><td><b>Request Updated</b></td><td>' + date_updated + '</td></tr><tr><td><b>Workout ID</b></td><td>' + entryId + '</td></tr></table>')
                
                logging.info('Entry updated, action logged to Slack thread, requestor emailed.')
            else:
                logging.error('Could not approve entry ' + entryId)
                self.slack.post_msg_to_channel(text='Map Request Approval Failed! ' + user_name + ' tried to approve it, the system failed. Call admin.', thread_ts=body['container']['message_ts'])

        elif action == Action_Value.Refresh.name:
            logging.info('Action: Refresh')

            entryId = action_value_pieces[1]
            entry = self.gravity_forms.get_entry(entryId)
            blocks = self._build_workout_slack_blocks(entry=entry)
            self.slack.replace_msg(original_message=body['message'], ts=body['container']['message_ts'], blocks=blocks)

        elif action == Action_Value.MarkComplete.name:
            logging.info('Action: Mark Complete')

            statusBlock = Slack.get_block_section('Request manually marked approved by <@' + body['user']['id'] + '> at ' + Slack.convert_ts_to_et(body['actions'][0]['action_ts']))
            blocks = Slack.replace_buttons(blocks=body['message']['blocks'], newBlock=statusBlock)
            self.slack.replace_msg(original_message=body['message'], ts=body['container']['message_ts'], blocks=blocks)
        
        elif action == Action_Value.Delete.name:
            logging.info('Action: Delete')

            entryId = action_value_pieces[1]
            entry = self.gravity_forms.get_entry(entryId)

            if entry['status'] == 'trash':
                logging.warning('Entry ' + entryId + ' has already been deleted. No action will be taken on workout. Updating Slack post to remove buttons.')
                
                statusBlock = Slack.get_block_section('This workout was already deleted. Sorry about that. You should be good to go.')
                blocks = Slack.replace_buttons(blocks=body['message']['blocks'], newBlock=statusBlock)
                self.slack.replace_msg(original_message=body['message'], ts=body['container']['message_ts'], blocks=blocks)
                return

            deleteEntryId = action_value_pieces[2] # Entry ID of the form submitted to request the deletion, not the ID of the workout.
            deleteEntry = self.gravity_forms.get_entry(deleteEntryId)

            logging.info('Sending delete command for workout entry ' + entryId + '.')
            success = self.gravity_forms.trash_entry(entryId)
            if success:
                statusBlock = Slack.get_block_section('Workout sent to trash by <@' + body['user']['id'] + '> at ' + Slack.convert_ts_to_et(body['actions'][0]['action_ts']))
                blocks = Slack.replace_buttons(blocks=body['message']['blocks'], newBlock=statusBlock)
                self.slack.replace_msg(original_message=body['message'], ts=body['container']['message_ts'], blocks=blocks)
                
                region = deleteEntry['7']
                workout_name = deleteEntry['1']
                reason = deleteEntry['5']
                submitter_name = deleteEntry['4']
                submitter_email = deleteEntry['3']
                date_created = GravityForms.convert_date_to_et(deleteEntry['date_created'])
                date_updated = GravityForms.convert_date_to_et(deleteEntry['date_updated'])

                weekday = entry['14']
                time = entry['4']
                workout_type = entry['5']
                
                self.smtp.send_email('Map Pin Deleted', [submitter_email], '<div style="display: none; max-height: 0px; overflow: hidden;">Delete -> ' + workout_name + ' @ ' + region + '</div><div style="display: none; max-height: 0px; overflow: hidden;">&#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy;</div><p>Your request to remove a workout from <a href="https://map.f3nation.com">the map</a> has been approved; it should disappear within the hour. If you deleted this by mistake, or have any other issues, please reply to this email.</p><table border="1" style="border-collapse:collapse" cellpadding="5"><tr><td><b>Region</b></td><td>' + region + '</td></tr><tr><td><b>Workout Name</b></td><td>' + workout_name + '</td></tr><tr><td><b>Weekday</b></td><td>' + weekday + '</td></tr><tr><td><b>Time</b></td><td>' + time + '</td></tr><tr><td><b>Type</b></td><td>' + workout_type + '</td></tr><tr><td><b>Reason for deletion</b></td><td>' + reason + '</td></tr><tr><td><b>Submitter</b></td><td>' + submitter_name + '</td></tr><tr><td><b>Submitter Email</b></td><td>' + submitter_email + '</td></tr><tr><td><b>Request Created</b></td><td>' + date_created + '</td></tr><tr><td><b>Request Updated</b></td><td>' + date_updated + '</td></tr><tr><td><b>Workout ID</b></td><td>' + entryId + '</td></tr></table>')

                logging.info('Entry deleted, action logged to Slack, requestor emailed.')
            else:
                self.slack.post_msg_to_channel(text='Workout deletion failed! ' + user_name + ' tried to send it to trash, the system failed. Call admin.', thread_ts=body['container']['message_ts'])

            deleteEntry['is_approved'] = "1"
            deleteEntry['is_read'] = "1"
            logging.info('Marking delete request entry ' + deleteEntryId + ' as read and approved.')
            self.gravity_forms.update_entry(deleteEntryId, deleteEntry)

        elif action == Action_Value.RejectDelete.name:
            logging.info('Action: Reject Delete')

            entryId = action_value_pieces[1]
            logging.info('Sending delete command for delete request entry ' + entryId + '.')
            success = self.gravity_forms.trash_entry(entryId)
            if success:
                statusBlock = Slack.get_block_section('Workout will not be sent to trash, as indicated by <@' + body['user']['id'] + '> at ' + Slack.convert_ts_to_et(body['actions'][0]['action_ts']))
                blocks = Slack.replace_buttons(blocks=body['message']['blocks'], newBlock=statusBlock)
                self.slack.replace_msg(original_message=body['message'], ts=body['container']['message_ts'], blocks=blocks)

                region = entry['7']
                workout_name = entry['1']
                reason = entry['5']
                submitter_name = entry['4']
                submitter_email = entry['3']
                date_created = GravityForms.convert_date_to_et(entry['date_created'])
                date_updated = GravityForms.convert_date_to_et(entry['date_updated'])
                
                self.smtp.send_email('Map Pin NOT Deleted', [submitter_email], '<div style="display: none; max-height: 0px; overflow: hidden;">Delete -> ' + workout_name + ' @ ' + region + '</div><div style="display: none; max-height: 0px; overflow: hidden;">&#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy;</div><p>A map admin has opted <u>NOT</u> to delete this workout. If this is a surprise, and you would like to find out more, please reply to this email.</p><table border="1" style="border-collapse:collapse" cellpadding="5"><tr><td><b>Region</b></td><td>' + region + '</td></tr><tr><td><b>Workout Name</b></td><td>' + workout_name + '</td></tr><tr><td><b>Reason for deletion</b></td><td>' + reason + '</td></tr><tr><td><b>Submitter</b></td><td>' + submitter_name + '</td></tr><tr><td><b>Submitter Email</b></td><td>' + submitter_email + '</td></tr><tr><td><b>Request Created</b></td><td>' + date_created + '</td></tr><tr><td><b>Request Updated</b></td><td>' + date_updated + '</td></tr></table>')

                logging.info('Delete request entry (not workout) sent to trash, action logged to Slack, requestor emailed.')
            else:
                self.slack.post_msg_to_channel(text='Workout delete rejection failed! ' + user_name + ' tried to not send it to trash, the system failed. Call admin.', thread_ts=body['container']['message_ts'])

        elif action == Action_Value.Edit.name:
            logging.info('Action: Edit')
            
            blocks_loading = [Slack.get_block_section('We will be right with you.')]
            response = self.slack.open_modal(interactivePayload=body, title='Loading workout data', blocks=blocks_loading)
            
            entryId = action_value_pieces[1]
            entry = self.gravity_forms.get_entry(entryId)

            region = entry['21']
            workout_name = entry['2']

            callback_id = Views.EditWorkout.name + '_' + body['container']['message_ts'] + '_' + entryId
            blocks = self._build_edit_view_content(entry)
            self.slack.update_modal(view_id=response['view']['id'], callback_id=callback_id, title=workout_name + ' @ ' + region, blocks=blocks)

        else:
            logging.error('A Slack Action was received with an action value that is not handled: ' + action_value)

        logging.info('Done handling Slack Action.')
    

    def handle_slack_view_submission(self, body: dict):
        logging.debug(body)
        logging.info('Handling Slack View Submission.')

        callback_id = body['view']['callback_id']
        callback_pieces = str.split(callback_id, '_')
        callback_type = callback_pieces[0]

        if callback_type == Views.EditWorkout.name:
            message_ts = callback_pieces[1]
            
            entryId = callback_pieces[2]
            entry = self.gravity_forms.get_entry(entryId)

            edited = False
            if body['view']['state']['values']['workout_name']['workout_name']['value'] != entry['2']:
                entry['2'] = body['view']['state']['values']['workout_name']['workout_name']['value']
                edited = True
            
            if body['view']['state']['values']['street_1']['street_1']['value'] != entry['1.1']:
                entry['1.1'] = body['view']['state']['values']['street_1']['street_1']['value']
                edited = True

            if body['view']['state']['values']['street_2']['street_2']['value'] != entry['1.2']:
                entry['1.2'] = body['view']['state']['values']['street_2']['street_2']['value']
                edited = True

            if body['view']['state']['values']['city']['city']['value'] != entry['1.3']:
                entry['1.3'] = body['view']['state']['values']['city']['city']['value']
                edited = True

            if body['view']['state']['values']['state']['state']['value'] != entry['1.4']:
                entry['1.4'] = body['view']['state']['values']['state']['state']['value']
                edited = True

            if body['view']['state']['values']['zip_code']['zip_code']['value'] != entry['1.5']:
                entry['1.5'] = body['view']['state']['values']['zip_code']['zip_code']['value']
                edited = True

            if body['view']['state']['values']['latitude']['latitude']['value'] != entry['13']:
                entry['13'] = body['view']['state']['values']['latitude']['latitude']['value']
                edited = True

            if body['view']['state']['values']['longitude']['longitude']['value'] != entry['12']:
                entry['12'] = body['view']['state']['values']['longitude']['longitude']['value']
                edited = True

            if body['view']['state']['values']['website']['website']['value'] != entry['17']:
                entry['17'] = body['view']['state']['values']['website']['website']['value']
                edited = True

            if body['view']['state']['values']['notes']['notes']['value'] != entry['15']:
                entry['15'] = body['view']['state']['values']['notes']['notes']['value']
                edited = True
            
            if body['view']['state']['values']['submitter_name']['submitter_name']['value'] != entry['18']:
                entry['18'] = body['view']['state']['values']['submitter_name']['submitter_name']['value']
                edited = True
            
            if body['view']['state']['values']['submitter_email']['submitter_email']['value'] != entry['19']:
                entry['15'] = body['view']['state']['values']['submitter_email']['submitter_email']['value']
                edited = True

            if edited:
                logging.info('Updating some values for ' + entryId + '.')
                self.gravity_forms.update_entry(entryId=entryId, entry=entry)
            else:
                logging.info('No changes detected. No action taken.')
                #return

            logging.info('Refreshing message.')
            entry = self.gravity_forms.get_entry(entryId)
            blocks = self._build_workout_slack_blocks(entry=entry)
            message = self.slack.get_msg(message_ts)
            self.slack.replace_msg(original_message=message, ts=message_ts, blocks=blocks)
        
        logging.info('Dond handling Slack View Submission.')


    def handle_unapproved_workout_check(self, alert_on_no_unapproved: bool, include_channel_mention_on_alert: bool) -> None:
        logging.info('Handline Check Unapproved.')
        unapprovedUpdateCount = self.gravity_forms.get_unapproved_count(self.gravity_forms.FORM_ID_WORKOUT)
        unapprovedDeleteCount = self.gravity_forms.get_unapproved_count(self.gravity_forms.FORM_ID_WORKOUT_DELETE)

        if unapprovedUpdateCount == 0 & unapprovedDeleteCount == 0:
            logging.info('No unapproved.')
            if alert_on_no_unapproved:
                self.slack.post_msg_to_channel(text='There are no unapproved requests pending.')
            
            return
        
        unapprovedCounts = []
        if unapprovedUpdateCount > 0:
            unapprovedCounts.append(str(unapprovedUpdateCount) + ' <' + self.gravity_forms.BASE_URL + '/wp-admin/admin.php?page=gf_entries&filter=gv_unapproved&id=' + self.gravity_forms.FORM_ID_WORKOUT + '|updates>')
        if unapprovedDeleteCount > 0:
            unapprovedCounts.append(str(unapprovedDeleteCount) + ' <' + self.gravity_forms.BASE_URL + '/wp-admin/admin.php?page=gf_entries&filter=gv_unapproved&id=' + self.gravity_forms.FORM_ID_WORKOUT_DELETE + '|deletes>')
        
        if include_channel_mention_on_alert:
            message_intro = '<!channel>, there are unapproved requests: '
        else:
            message_intro = 'There are unapproved requests: '

        blocks = Slack.start_blocks()
        blocks.append(Slack.get_block_section(message_intro + ', '.join(unapprovedCounts) + '.'))

        self.slack.post_msg_to_channel(text='There are unapproved requests!', blocks=blocks)
        logging.info('Sent unapproved counts to Slack. Done handling.')