# -*- coding: UTF-8 -*-
# Import system modules
import datetime
import os
import random
import string
import traceback
import pickle

# Import 3rd-Party Dependencies
import flask
from flask_cors import CORS
from flask import (
    Flask, abort, request
)
from flask_socketio import SocketIO
from werkzeug.serving import WSGIRequestHandler

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)

# Import local modules
import database as db
import event as e
import responder
import environment

##############################
# Application & variable initialization
##############################
# Initialize Flask
app = Flask(__name__)
cors = CORS(app, resources={r"/foo": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')

WSGIRequestHandler.protocol_version = "HTTP/1.1"

environment.environment.set_env("development")
environment.environment.lock()

keys = environment.get_key(environment.environment.get_env())
# Channel Access Token
line_bot_api = LineBotApi(keys[0])
# Channel Secret
handler = WebhookHandler(keys[1])

##############################
# Callback API
##############################
# Listen to all POST requests from HOST/callback

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    # app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# API for triggering event.high_temp case
# Accepts a json file with line_id and

@app.route("/event_high_temp", methods=["POST"])
def high_temp():
    if request.headers["Content-Type"] != "application/json":
        return abort(400, "Bad Request: Please use `json` format")
    try:
        # Known issue user name and birthday conflict
        data = request.json
        user_id = db.get_user_id(birth=data["birth"], name=data["name"])
        if user_id is None:
            raise ValueError(
                f"User ID not found:\nUsername: {data['name']}\nUser BDay: {data['birth']}")
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(404, "Not Found: User ID not found")

    status = db.update_status(status="s1s0", user_id=user_id)
    responder.high_temp(
        event=None,
        socketio=socketio,
        status=status,
        user_id=user_id
    )
    return "OK"

#########################
# Scenario 2
#########################

# @app.route("/event_push_news")
# def push_news():
#     users = session.get_users()
#     for user_id in users:
#         print(f'User: {user_id}')
#         stat = 's2s0'
#         session.switch_status(user_id, stat)
#         responder.push_news(user_id)
#     pass

#########################
# Frontend API
#########################

@app.route("/users", methods=['POST'])
# @cross_origin(origin='*',headers=['Content-Type','Authorization'])
def get_user():
    '''
    - input: none
    - output:
        array[{
            user_id
            user_name,
            last_content,     //最後一個訊息的內容
            timestamp,        //最後一個訊息的時間
        }]
    '''
    # TODO: Verify request from frontend (Call function)
    try:
        data = request.get_json(force=True)
        token = data["auth_token"]
        if not auth_valid(token):
            raise ValueError(f"Invalid token {token}")
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(403, 'Forbidden: Authentication is bad')

    users = db.get_users()
    temp = []

    for user_id, user_name in users:
        last_msg, timestamp = db.get_last_message(user_id=user_id)
        temp.append({
            "user_id": user_id,
            "user_name": user_name,
            "last_content": last_msg,
            "timestamp": timestamp
        })

    response = flask.Response(str(temp))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route("/messages", methods=['POST'])
def get_old_msgs():
    '''
    - input:
        - user_id: string
        - timestamp_offset: timestamp
        - maxAmount: int
    - output:
        array[{
            msg_id,
            user_id,
            user_name,
            direction,
            content,
            timestamp,
        }]
    '''

    data = request.get_json(force=True)
    try:
        token = data["auth_token"]
        if not auth_valid(token):
            raise ValueError(f"Invalid token {token}")
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(403, "Forbidden: Authentication is bad")

    user_id = data["user_id"]
    offset = data["timestamp_offset"]
    max_amount = data["max_amount"]

    messages = db.get_messages(user_id=user_id)
    filtered = []

    # Get offset time (-1 == now)
    if offset == -1:
        offset = datetime.datetime.now().timestamp()
    elif isinstance(offset, str):
        offset = float(offset)
        # offset = datetime.datetime.fromtimestamp(offset)

    # Filter messages that are > timestamp
    for message in messages:
        message = list(message)
        # message[4] = datetime.datetime.fromtimestamp(float(message[4]))
        if float(message[4]) < offset:
            filtered.append(message)

    temp = []

    if len(filtered) >= max_amount:
        for count in range(max_amount):
            temp.append({
                "msg_id": filtered[count][0],
                "user_id": user_id,
                "user_name": db.get_user_name(user_id=filtered[count][1]),
                "content": filtered[count][2],
                "direction": filtered[count][3],
                "timestamp": filtered[count][4],
            })
    else:
        for message in filtered:
            temp.append({
                "msg_id": message[0],
                "user_name": db.get_user_name(user_id=message[1]),
                "content": message[2],
                "direction": message[3],
                "timestamp": message[4],
            })

    response = flask.Response(str(temp))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route("/send", methods=['POST'])
def send_msg():
    try:
        data = request.get_json(force=True)
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(400, 'Bad Request: Error parsing to `json` format')
    try:
        token = data["auth_token"]
        if not auth_valid(token):
            raise ValueError(f"Invalid token {token}")
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(403, 'Forbidden: Authentication is bad')

    user_id = data["user_id"]
    message = data["message"]

    try:
        message = TextSendMessage(text=message)
        line_bot_api.push_message(user_id, message)
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(400, "Bad request: invalid message")

    frontend_data = {
        "user_name": db.get_user_name(user_id=user_id),
        "user_id": user_id,
        "content": data["message"],
        "direction": 1,
    }

    db.log(
        direction=1,
        message=data["message"],
        user_id=user_id
    )

    print(f"SOCKET: Sending to Front-End\n{data['message']}")
    socketio.emit('Message', frontend_data, json=True, broadcast=True)
    print("SOCKET: Emitted to Front-End")

    response = flask.Response("OK")
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# @app.route("/broadcast", methods=['POST'])
# def broadcast_msg():
#     users = db.get_users()
#     for user in users:
#         send_msg()

@app.route("/login", methods=['POST'])
def log_in():
    try:
        data = request.get_json(force=True)
        username = data["username"]
        psw = data["password"]
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        response = flask.Response(status=400)
        return response

    result = db.get_admin()
    for res in result:
        if res[1] == psw:
            success = True
            break
        else:
            success = False

    if success:
        token = find_token_of_admin(username)
        if token is None:
            token = generate_token(username)
        response = flask.Response(response=token, status=200)

    elif not success:
        response = flask.Response(status=401)

    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

#########################
# Authentication variables and functions
#########################

auths = {}

def generate_token(username):
    size = 15
    token = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=size))
    auths[token] = username
    return token

def find_token_of_admin(username):
    for token, value in auths.items():
        if value == username:
            return token
    return None

def auth_valid(token):
    if len(auths.keys()) > 0:
        for key in auths:
            if key == token:
                return True

    return False

# TODO: Save when signal interrupted

def save_auths():
    path = "session/admin.pickle"
    with open(path, "wb") as fb:
        pickle.dump(auths, fb)

def get_auths():
    path = "session/admin.pickle"
    with open(path, "rb") as fb:
        pickle.load(fb)

#########################
# socket connection
#########################

@socketio.on('connect', namespace="/")
def handle_connection():
    try:
        token = request.args.get('auth_token')
        if not auth_valid(token):
            raise ValueError(f"Invalid token {token}")
        print('SOCKET: Connected')
        socketio.emit('Response', {"data": "OK"}, broadcast=True)
        print('SOCKET: Emitted')
        return
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(403, 'Forbidden: Authentication is bad')


@socketio.on_error()
def error_handler_chat(err):
    print(err)

##############################
# Message handler
##############################
# Text message handler
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    '''
    Pass id, msg, and session into event function and return updated status
    Respond to user according to new status
    '''
    # Print event metadata
    # print(event)

    # Retreive user metadata
    user_id = event.source.user_id
    user_msg = event.message.text
    # Converted from JavaScript milisecond to second
    timestamp = event.timestamp/1000

    # TODO: check timeout
    status = db.get_status(user_id=user_id)

    if status is None:
        db.add_user(user_id=user_id)
        status = db.get_status(user_id=user_id)

    # Log user metadata
    print(f'\nUser: {user_id}')
    print(f'Message: {user_msg}')
    print(f'Status: {status}\n')

    # Send user message to frontend
    responder.send_frontend(
        direction=0,
        socketio=socketio,
        user_id=user_id,
        message=user_msg
    )

    # Log user message to database
    db.log(
        direction=0,
        timestamp=timestamp,
        message=user_msg,
        user_id=user_id
    )

    # User in registration
    if status in ["r", "r0", "r1", "r_err"]:
        status = e.registration(
            message=user_msg,
            status=status,
            user_id=user_id
        )
        responder.registration(
            event=event,
            socketio=socketio,
            status=status
        )

    # User trigger QA
    elif status == "s" and user_msg == '/qa':
        status = "qa0"
        db.update_status(
            status=status,
            user_id=user_id,
        )
        responder.qa(
            event=event,
            socketio=socketio,
            status=status
        )

    elif status in ["qa0", "qa1", "qa2_f"]:
        status = e.qa(
            event=event,
            status=status
        )
        responder.qa(
            event=event,
            socketio=socketio,
            status=status
        )

    # User in scenario 1
    elif status in ["s1s0", "s1s1", "s1d0", "s1d1", "s1d2",
                    "s1d3", "s1d4", "s1d5", "s1df", "s1s2",
                    "s1s3", "s1s4"]:
        status = e.high_temp(
            event=event,
            status=status
        )
        responder.high_temp(
            event=event,
            socketio=socketio,
            status=status,
            user_id=user_id
        )

    #########################
    # TODO: User in scenario 2
    #########################
    # elif status in ["s2s1", "s2s2", "s2s3"]:
    #     status = e.push_news(user_id, user_msg, session)
    #     responder.push_news(event, session)

##############################
# Main function
##############################

if __name__ == "__main__":
    # Setup host port
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
