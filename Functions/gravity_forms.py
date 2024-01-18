import os
import requests

class GravityForms:
    BASE_URL = os.getenv('GRAVITY_FORMS_BASE_URL')
    FORM_ID_WORKOUT = os.getenv('GRAVITY_FORM_WORKOUT_FORM_ID')
    FORM_ID_WORKOUT_DELETE = os.getenv('GRAVITY_FORM_DELETE_FORM_ID')
    KEY = os.getenv('GRAVITY_FORM_KEY')
    SECRET = os.getenv('GRAVITY_FORM_SECRET')
    
    def get_unapproved_count(self, formId: str) -> int:
        param = {"search": '{"field_filters": [{"key":"is_approved","value":3,"operator":"="}]}'}
        response = requests.get(self.BASE_URL + '/wp-json/gf/v2/forms/' + formId + '/entries', params=param, auth=(self.KEY, self.SECRET))
        response.encoding = 'utf-8-sig'
        body = response.json()

        return int(body['total_count'])
    

    def get_entry(self, entryId: str) -> dict:
        response = requests.get(self.BASE_URL + '/wp-json/gf/v2/entries/' + entryId, auth=(self.KEY, self.SECRET))
        response.encoding = 'utf-8-sig'
        entry = response.json()

        return entry


    def update_entry(self, entryId: str, entry: dict) -> bool:
        """Updates indicated entry with the json provided. Will return True if response from Gravity Forms is 200."""

        response = requests.put(self.BASE_URL + '/wp-json/gf/v2/entries/' + entryId, json=entry, auth=(self.KEY, self.SECRET))

        return response.status_code == 200


    def trash_entry(self, entryId: str) -> bool:
        """Moves indicated entry to the trash. Will return True if response from Gravity Forms is 200."""

        response = requests.delete(self.BASE_URL + '/wp-json/gf/v2/entries/' + entryId, auth=(self.KEY, self.SECRET))

        return response.status_code == 200
    
    def is_new_or_update(entry: dict) -> str:
        """Takes a Gravity Form entry and returns a string indicating if the submission is 'New' or 'Updated'."""

        if entry['date_created'] == entry['date_updated']:
            return 'New'
        else:
            return 'Update'