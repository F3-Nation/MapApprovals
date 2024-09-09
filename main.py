import os
from flask import Flask, request, Response, send_from_directory
from dotenv import load_dotenv
from threading import Thread
import logging
import json
import google.cloud.logging
from handlers.map_approval import MapApprovalHandler
from services.google_sheets import GoogleSheets

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
googleLoggingClient = google.cloud.logging.Client()
googleLoggingClient.setup_logging()

map_approval = MapApprovalHandler()

app = Flask(__name__)


@app.route('/')
def status():
    return Response('Service is running.', 200)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')


@app.route('/webhooks/gravityforms/workout', methods=['POST'])
def process_gravity_forms_workout():
    thread = Thread(target=map_approval.handle_gravity_forms_submission, kwargs={'entry':request.json})
    thread.start()
    return Response(status=200)


@app.route('/webhooks/gravityforms/workoutdelete', methods=['POST'])
def process_gravity_forms_workout_delete():
    thread = Thread(target=map_approval.handle_gravity_forms_delete, kwargs={'entry':request.json})
    thread.start()
    return Response(status=200)


@app.route('/webhooks/slack', methods=['POST'])
def process_slack():
    body = json.loads(request.form['payload'])
    logging.debug(body)

    if body['type'] == 'block_actions':
        thread = Thread(target=map_approval.handle_slack_action, kwargs={'body':body})
    elif body['type'] == 'view_submission':
        thread = Thread(target=map_approval.handle_slack_view_submission, kwargs={'body':body})
    else:
        logging.warning('Received an interactive message from Slack with an unhandled type: ' + body['type'])
        return Response(status=400)

    thread.start()
    return Response(status=200)


@app.route('/webhooks/checkunapproved', methods=['POST'])
def process_unapproved_workout_check():
    params = request.args
    check_type = len(params) > 0 and 'type' in params and params['type']
    alert_on_no_unapproved = len(params) > 0 and 'alertonnounapproved' in params and params['alertonnounapproved']
    include_channel_mention_on_alert = len(params) > 0 and 'includechannelmentiononalert' in params and params['includechannelmentiononalert']

    if check_type != 'workouts' and check_type != 'regions':
        return Response('Must include parameter called "type" with value "workouts" or "regions" (field name and value are case-sensative).', status=400)
    
    if check_type == 'workouts':
        target_handler = map_approval.handle_unapproved_workout_check
    else:
        target_handler = map_approval.handle_unapproved_region_check

    thread = Thread(target=target_handler, kwargs={'alert_on_no_unapproved':alert_on_no_unapproved, 'include_channel_mention_on_alert':include_channel_mention_on_alert})
    thread.start()
    return Response(status=200)


if __name__ == "__main__":
    logging.info('Starting up app')
    load_dotenv()
    app.run(port=8080, debug=False)