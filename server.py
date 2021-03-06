from flask import Flask, request, render_template, jsonify
from flask_cors import CORS, cross_origin
from twilio.rest import Client
import os
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
import json
from message_helper import message_helper
from create_twilio_message import create_twilio_message

# Set up authentication
project_folder = os.path.expanduser('~/Google Drive/Programming/sms-steve-backend')
load_dotenv(os.path.join(project_folder, '.env'))
account_sid = os.getenv('ACCOUNT_SID')
auth_token = os.getenv('AUTH_TOKEN')
client = Client(account_sid, auth_token)

# Number settings
to_number = os.getenv('TO_NUMBER')
from_number = os.getenv('FROM_NUMBER')

# Define the app
app = Flask(
    __name__,
    static_folder="build/static",
    template_folder="build"
)
app.config['CORS_HEADERS'] = 'Content-Type'

CORS(app, resources={r"/api/*": {"origins": "*"}})
# TODO: figure out how to limit the origins without breaking the dumb app. ["http://localhost:3000/", "https://stevehind.github.io/sms-steve/"]

@app.route("/", methods = ['GET'])
def home():
    return "This is an Easter Egg. Happy Easter. Go to https://stevehind.me"

# Handle the pre-validation from browser
@app.route("/api/v1/web-sms", methods = ['OPTIONS'])
def sms_options():
    return jsonify("This message exists."), 200

# Send a message to Steve
@app.route("/api/v1/web-sms", methods = ['GET', 'POST'])
def sms_steve():
    custom = False

    # Handle the input and configure the message
    try:
        request_data = json.loads(request.data)

        print(request_data)

        input_text = request_data['message']
        name = request_data['name']
        sender_number = request_data['number']
        body_message = message_helper(name, input_text, sender_number)
        custom = True
        
    except Exception:
        body_message = "Someone sent an SMS, but there was no custom message."

     # Send the message
    try:
        message = create_twilio_message(body_message, to_number)

        print(message.sid)

        if custom:
            response = jsonify("Custom message sent to Steve.")
            response.headers.add('Access-Control-Allow-Origin', "*")
            return response, 200
        else:
            return jsonify("Default message sent to Steve."), 200
    
    except Exception as e:
        return str(e), 400

# Twilio webhook testing command:
# LOCAL: twilio phone-numbers:update "+12244878383" --sms-url="http://localhost:5000/sms"
# DEPLOYED: twilio phone-numbers:update "+12244878383" --sms-url="https://sms-22448-steve.herokuapp.com/sms"

# Reply to inbound messages
@app.route("/api/v1/sms", methods = ['GET', 'POST'])
def reply_to_sms():
    # Give a contextual reply to the inbound
    try:
        payload = request.values
        inbound_number = payload.get('From', None)
        inbound_message = payload.get('Body', None)

        response_message = "Steve received your message and has your contact details."

        response = MessagingResponse()
        response.message(response_message) 

        message_to_steve = message_helper("Unknown SMS sender", inbound_message, inbound_number)
        create_twilio_message(message_to_steve, to_number)

        return str(response)

    # If there's an error, let the sender know
    except Exception as e:
        print(str(e))
        error_response = MessagingResponse()
        error_response.message("Something went wrong. No SMS was sent to Steve.")
        return str(error_response)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug = True)