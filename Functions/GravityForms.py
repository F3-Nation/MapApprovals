import logging
import os


class GravityForms:
    def __init__(self, slack_client):
        self.slack_client = slack_client

    def handle_gravity_forms_submission(self, body: dict):
        logging.info('Handling Gravity Forms Workout.')
        logging.debug(body)

        if 'form_id' not in body:
            logging.error('Not a proper Gravity Forms payload. Payload does not include "form_id", which represents the form ID, and is required. Will not process')
            return

        if body['form_id'] != os.getenv('GRAVITY_FORM_WORKOUT_FORM_ID'):
            logging.error('Form ID submitted to the /webhooks/workout endpoint (' + body['form_id'] + ' does not match configured form ID (' + os.getenv('GRAVITY_FORM_WORKOUT_FORM_ID') + '). Will not process.')
            return

        blocks = self.slack_client.build_new_or_update_msg(body)
        region = body['21']

        self.slack_client.post_msg_to_channel('Map Request from ' + region, blocks)

    def handle_gravity_forms_delete(self, body: dict):
        logging.info('Handling Gravity Forms Workout Delete.')
        logging.debug(body)

        if 'form_id' not in body:
            logging.error('Not a proper Gravity Forms payload. Payload does not include "form_id", which represents the form ID, and is required. Will not process')
            return

        if body['form_id'] != os.getenv('GRAVITY_FORM_DELETE_FORM_ID'):
            logging.error('Form ID submitted to the /webhooks/workoutdelete endpoint (' + body['form_id'] + ' does not match configured form ID (' + os.getenv('GRAVITY_FORM_DELETE_FORM_ID') + '). Will not process.')
            return

        blocks = self.slack_client.build_delete_message(body)
        region = body['7']

        self.slack_client.post_msg_to_channel('Map Delete Request from ' + region, blocks)

