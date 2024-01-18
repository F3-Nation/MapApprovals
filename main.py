import os
from flask import Flask, request, Response, send_from_directory
from dotenv import load_dotenv
from threading import Thread
import logging
import json
import google.cloud.logging
from handlers.map_approval import MapApprovalHandler

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
def processGravityFormsWorkout():
    thread = Thread(target=map_approval.handle_gravity_forms_submission, kwargs={'entry':request.json})
    thread.start()
    return Response(status=200)


@app.route('/webhooks/gravityforms/workoutdelete', methods=['POST'])
def processGravityFormsWorkoutDelete():
    thread = Thread(target=map_approval.handle_gravity_forms_delete, kwargs={'entry':request.json})
    thread.start()
    return Response(status=200)


@app.route('/webhooks/slack', methods=['POST'])
def processSlack():
    body = json.loads(request.form['payload'])

    if body['type'] == 'block_actions':
        thread = Thread(target=map_approval.handle_slack_action, kwargs={'body':body})
    else:
        logging.warning('Received an interactive message from Slack with an unhandled type: ' + body['type'])
        return Response(status=400)

    thread.start()
    return Response(status=200)


@app.route('/triggers/checkunapproved')
def checkForUnapprovedWorkouts():
    thread = Thread(target=map_approval.handleCheckUnapprovedTrigger)
    thread.start()
    return Response(status=200)


if __name__ == "__main__":
    logging.info('Starting up app')
    load_dotenv()
    app.run(port=8080, debug=False)