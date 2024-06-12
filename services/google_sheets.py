import os
import requests
import logging

class GoogleSheets:
    WORKOUT_HISTORY_SPREADSHEETURL = os.getenv('WORKOUT_HISTORY_SPREADSHEETURL')

    def get_single_entity(self, entryId: str) -> dict:
        param = {"dataset":"workouts","entryid": entryId}
        response = requests.get(self.WORKOUT_HISTORY_SPREADSHEETURL, params=param)
        response.encoding = 'utf-8-sig'
        body = response.json()

        if body["Status"] != 200:
            logging.error("Failed to successfully pull historical workout data from Google Sheets using Entry ID '" + entryId + "'. Error: " + body["Message"])
            return {}

        data = body["Data"]
        entity = {}
        
        for field in range(len(data[0])-1):
            entity[data[0][field]] = data[1][field]

        return entity
