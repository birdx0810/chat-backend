# -*- coding: UTF-8 -*-
# Import 3rd-Party Dependencies
import flask as flask
from flask_cors import CORS, cross_origin
from flask import (
    Flask, abort, escape, request, redirect, url_for, jsonify
)
from flask_socketio import (
    SocketIO, send, emit
)

import eventlet

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, StickerMessage
)

# Import system modules
import datetime
import logging
import signal
import sys
import os
import hashlib
import json
import random
import string
import pickle

# Import local modules
import database as db
import event as e
import templates as t
import utilities
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

environment.environment.set_env("development")
environment.environment.lock()

keys = environment.get_key(environment.environment.get_env())
# Channel Access Token
line_bot_api = LineBotApi(keys[0])
# Channel Secret
handler = WebhookHandler(keys[1])

# Initialize Session
session = utilities.Session()

##############################
# Chatbot API
##############################
# Listen to all POST requests from HOST/callback


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# API for triggering event.high_temp case
# Accepts a json file with line_id and


@app.route('/event_high_temp', methods=['POST'])
def high_temp():
    if request.headers['Content-Type'] != 'application/json':
        return abort(400, 'Bad Request: Please use `json` format')
    elif request.method != 'POST':
        return abort(403, 'Forbidden: Please use `POST` request')
    try:
        data = request.json
        user_id = db.get_user_id(data['name'], data['birth'])
        if user_id == None:
            raise ValueError(
                f"User ID not found:\nUsername: {data['name']}\nUser BDay: {data['birth']}")
    except ValueError as e:
        traceback.format_exc()

        print(traceback.format_exc())
        return abort(404, 'Not Found: User ID not found')

    user_id = user_id[0][0]
    stat = 's1s0'
    session.switch_status(user_id, stat)
    responder.high_temp_resp(user_id, socketio)
    return "OK"


@app.route("/event_push_news")
def push_news():
    users = session.get_users()
    for user_id in users:
        print(f'User: {user_id}')
        stat = 's2s0'
        session.switch_status(user_id, stat)
        responder.push_news_resp(user_id)
    pass

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
        assert(auth_valid(token))
    except:
        return abort(403, 'Forbidden: Authentication is bad')

    users = db.get_users()
    temp = []

    for user_id, username in users:
        temp.append({
            "user_id": user_id,
            "user_name": username,
            "last_content": session.status[user_id]["last_msg"],
            "timestamp": session.status[user_id]["sess_time"],
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
        assert(auth_valid(token))
    except:
        return abort(403, "Forbidden: Authentication is bad")

    user_id = data["user_id"]
    offset = data["timestamp_offset"]
    max_amount = data["max_amount"]

    messages = db.get_messages(user_id)
    filtered = []

    # Get offset time (-1 == now)
    if offset == -1:
        offset = datetime.datetime.now().timestamp()
    elif type(offset) is str:
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
                "user_name":  session.status[filtered[count][1]]["user_name"],
                "content": filtered[count][2],
                "direction": filtered[count][3],
                "timestamp": filtered[count][4],
            })
    else:
        for message in filtered:
            temp.append({
                "msg_id": message[0],
                "user_name":  session.status[message[1]]["user_name"],
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
    except:
        return abort(400, 'Bad Request: Error parsing to `json` format')
    try:
        token = data["auth_token"]
        assert(auth_valid(token))
    except:
        return abort(403, 'Forbidden: Authentication is bad')

    user_id = data["user_id"]
    message = data["message"]

    try:
        message = TextSendMessage(text=message)
        line_bot_api.push_message(user_id, message)
    except:
        return abort(400, "Bad request: invalid message")

    frontend_data = {
        "user_name": session.status[user_id]["user_name"],
        "user_id": user_id,
        "content": data["message"],
        "direction": 1,
    }

    db.log(user_id, data["message"], direction=1)

    print(f"SOCKET: Sending to Front-End\n{data['message']}")
    socketio.emit('Message', frontend_data, json=True, broadcast=True)
    print("SOCKET: Emitted to Front-End")

    response = flask.Response("OK")
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route("/broadcast", methods=['POST'])
def broadcast_msg():
    users = db.get_users()
    for user in users:
        # send_msg()
        pass


@app.route("/login", methods=['POST'])
def log_in():
    try:
        data = request.get_json(force=True)
        username = data["username"]
        psw = data["password"]
    except:
        response = flask.Response(status=400)
        return response

    result = db.get_admin()
    for res in result:
        if res[1] == psw:
            success = True
            break
        else:
            success = False

    if success == True:
        token = find_token_of_admin(username)
        if token == None:
            token = generate_token(username)
        response = flask.Response(response=token, status=200)

    elif success == False:
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
        for key, value in auths.items():
            if key == token:
                return True
    else:
        return False

# TODO: Save when signal interrupted


def save_auths():
    path = "session/admin.pickle"
    with open(path, "wb") as f:
        pickle.dump(auths, f)


def get_auths():
    path = "session/admin.pickle"
    with open(path, "rb") as f:
        pickle.load(f)

#########################
# socket connection
#########################


@socketio.on('connect', namespace="/")
def handle_connection():
    try:
        token = request.args.get('auth_token')
        assert(auth_valid(token))
    except:
        return abort(403, 'Forbidden: Authentication is bad')
    print('SOCKET: Connected')
    socketio.emit('Response', {"data": "OK"}, broadcast=True)
    print('SOCKET: Emitted')


@socketio.on_error()
def error_handler_chat(e):
    print(e)



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
    status = db.get_status(user_id)

    if status == None:
        db.add_user(user_id)
        status = db.get_status(user_id)

    # Log user metadata
    print(f'\nUser: {user_id}')
    print(f'Message: {user_msg}')
    print(f'Status: {status}\n')

    # Send user message to frontend
    responder.send_frontend(user_id, user_msg, socketio=socketio, direction=0)

    # Log user message to database
    db.log(user_id, user_msg, direction=0, timestamp=timestamp)

    # User in registration
    if status in ["r", "r0", "r1", "r_err"]:
        status = e.registration(user_id, user_msg, status)
        responder.registration_resp(event, status, socketio)

    # User trigger QA
    elif status == "s" and user_msg == '/qa':
        status = "qa0"
        db.update_status(user_id, status)
        responder.qa_resp(event, status, socketio)

    elif status in ["qa0", "qa1", "qa2_f"]:
        status = e.qa(event, status)
        responder.qa_resp(event, status, socketio)

    # User in scenario 1
    elif status in ["s1s0", "s1s1", "s1d0", "s1d1", "s1d2", "s1d3", "s1d4", "s1d5", "s1d6", "s1s2", "s1s3", "s1s4"]:
        # Respond first then push...
        status = e.high_temp(event, session)
        responder.high_temp_resp(user_id, socketio, event)

    # TODO: User in scenario 2
    elif status in ["s2s1", "s2s2", "s2s3"]:
        status = e.push_news(user_id, user_msg, session)
        responder.push_news_resp(event, session)

    '''
    (DEPRECATED) User in chat state (currently unable to communicate)
    '''
    # else:
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="不好意思，我還不會講話...")
    #     )
    #     db.log(user_id, "不好意思，我還不會講話...", direction=1)


# Sticker message handler (echo)
'''
Stickers should not affect user status
'''


@handler.add(MessageEvent, message=StickerMessage)
def handle_message(event):
    # Retrieve message metadata
    id = event.message.id
    sticker_id = event.message.sticker_id
    package_id = event.message.package_id

    line_bot_api.reply_message(
        event.reply_token,
        StickerMessage(id=id, sticker_id=sticker_id, package_id=package_id)
    )
    pass

##############################
# Main function
##############################


if __name__ == "__main__":
    # Load session
    # session.load_session()

    client_status = {}

    # Hook interrupt signal
    # signal.signal(signal.SIGINT, session.signal_handler)

    # Setup host port
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)

    # Call function at apointed time
    # while True:
    #     time.sleep(3600*30)
    #     time = datetime.datetime.now().strftime("%H:%M")
    #     if time == "00:00":
    #         db.sync(session)
    # if time == 20:00:
    # TODO: Run news crawler
    # got_news = crawl()
    # if got_news:
    # TODO: Call news API
    # break
