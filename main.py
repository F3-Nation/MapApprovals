import os
from flask import Flask, request, Response, send_from_directory
from dotenv import load_dotenv
from threading import Thread
import logging
import json
from Functions.GravityForms import (
    handleGravityFormsSubmission
)
from Functions.Slack import (
    handleSlackAction
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

app = Flask(__name__)

@app.route('/')
def status():
    return Response('Service is running.', 200)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')

@app.route('/webhook/gravityforms', methods=['POST'])
def processGravityForms():
    thread = Thread(target=handleGravityFormsSubmission, kwargs={'body':request.json})
    thread.start()
    return Response(status=200)

@app.route('/webhook/slack', methods=['POST'])
def processSlack():
    body=json.loads(request.form['payload'])
    
    if body['type'] == 'block_actions':
        thread = Thread(target=handleSlackAction, kwargs={'body':body})
    else:
        logging.warning('Received an interactive message from Slack with an unhandled type: ' + body['type'])
        return Response(status=400)
        
    thread.start()
    return Response(status=200)

if __name__ == "__main__":
    logging.info('Starting up app')
    load_dotenv()
    app.run(port=8080, debug=False)