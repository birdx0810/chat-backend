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
import datetime, time, logging, signal, sys, os
import hashlib
import json
import random
import string

# Import local modules
import database as db
import event as e
import templates as t
import utilities, responder

##############################
# Application & variable initialization
##############################
# Initialize Flask
app = Flask(__name__)
cors = CORS(app, resources={r"/foo": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
socketio = SocketIO(app)

# Is development or production
is_development=True
if is_development:
    # Channel Access Token
    line_bot_api = LineBotApi('XEQclTuSIm6/pcNNB4W9a2DDX/KAbCBmZS4ltBl+g8q2IxwJyqdtgNNY9KtJJxfkuXbHmSdQPAqRWjAciP2IZgrvLoF3ZH2C2Hg+zZMgoy/xM/RbnoFa2eO9GV2F4E1qmjYxA0FbJm1uZkUms9o+4QdB04t89/1O/w1cDnyilFU=')
    # Channel Secret
    handler = WebhookHandler('fabfd7538c098fe222e8012e1df65740')
else: # Is production
    # Channel Access Token
    line_bot_api = LineBotApi('8kCwJkbO0Ps6ftZfFSJmBjmc+VrpNB0x4lMn+pEUNV4t306quG5AQKUnPGHNqw8sYFIQL7086mkTQdQj4iC/zUgwKRZMPHCKaxc5N1buQSY+rzGohXfiwldZbkTQQj/sDK7tv8URS5C9sx7kwkfQRAdB04t89/1O/w1cDnyilFU=')
    # Channel Secret
    handler = WebhookHandler('5e438935670953f040569105b3d527e1')

# Initialize Session
session = utilities.Session()

##############################
# API handler
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
    else:
        data = request.json
        userid = db.check_user(data['name'], data['birth'])
        if userid is None:
            return abort(400, 'Bad Request: User not found')

        # (condition.condition_diagnosis)
        # dialogue_code, message = res.condition_diagnosis.greeting()
        # sess.session_update_dialogue(userid,dialogue_code)
        # line_bot_api.push_message(userid, message)

        userid = userid[0][0]
        print(f'User: {userid}')
        stat = 's1s0'
        session.switch_status(userid, stat)
        responder.high_temp_resp(userid, session)
        return "OK"

@app.route("/event_push_news")
def push_news():
    users = session.get_users()
    for userid in users:
        print(f'User: {userid}')
        stat = 's2s0'
        session.switch_status(userid, stat)
        responder.push_news_resp(userid)
    pass

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
    #TODO: Verify request from frontend (Call function)
    #try:
    data = request.get_json(force=True)
    token = data["auth_token"]
    assert(auth_valid(token))
    #except:
        #return abort(403, 'Forbidden: Authentication is bad')

    users = db.get_users()
    temp = []

    for userid, username in users:
        temp.append({
            "user_id": userid,
            "user_name": username,
            "last_content": session.status[userid]["last_msg"],
            "timestamp": session.status[userid]["sess_time"],
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
    # try:
    #     data = request.get_json(force=True)
    # except:
    #     return abort(400, 'Bad Request: Error parsing to `json` format')
    # try:
    #     token = data["auth_token"]
    #     assert(auth_valid(token))
    # except:
    #     return abort(403, 'Forbidden: Authentication is bad')

    data = request.get_json(force=True)
    token = data["auth_token"]
    assert(auth_valid(token))

    userid = data["user_id"]
    offset = data["timestamp_offset"]
    max_amount = data["max_amount"]

    messages = db.get_messages(userid)
    filtered = []

    # Get offset time (-1 == now)
    if offset == -1:
        offset = datetime.datetime.now()
    elif type(offset) is str:
        offset = datetime.datetime.strptime(offset, "%Y-%m-%d %H:%M:%S")

    # Filter messages that are > timestamp
    for message in messages:
        message = list(message)
        message[4] = datetime.datetime.strptime(message[4], "%Y-%m-%d %H:%M:%S")
        if message[4] < offset:
            filtered.append(message)

    temp = []

    if len(filtered) >= max_amount:
        for count in range(max_amount):
            temp.append({
                "msg_id": filtered[count][0],
                "user_name":  session.status[filtered[count][1]]["user_name"],
                "content": filtered[count][2],
                "direction": filtered[count][3],
                "timestamp": filtered[count][4].strftime("%Y-%m-%d %H:%M:%S"),
            })
    else:
        for message in filtered:
            temp.append({
                "msg_id": message[0],
                "user_name":  session.status[message[1]]["user_name"],
                "content": message[2],
                "direction": message[3],
                "timestamp": message[4].strftime("%Y-%m-%d %H:%M:%S"),
            })

    response = flask.Response(str(temp))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@socketio.on('Connect to socket', namespace="/sync")
def handle_connection(json, methods=['GET', 'POST']):
    print('message was received!!!')
    socketio.emit('Response', {"data", "OK"})

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

    userid = data["user_id"]
    message = data["message"]
    db.log(userid, message, direction=1)

    message = TextSendMessage(text=message)
    line_bot_api.push_message(userid, message)

    response = flask.Response("OK")
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# Connect to message synchronizer
@socketio.on("Synchronize New Messages", namespace="/sync")
def sync_new_msgs(json, methods=['POST']):
    auth = json["auth_token"]
    print('received connection request from: ' + auth)
    socketio.emit('Connection', {"data": "Connection Established"})

@app.route("/chg_name", methods=['POST'])
def chg_name():
    #TODO: Change admin username

    pass

@app.route("/chg_pass", methods=['POST'])
def chg_pass():
    #TODO: Change admin password

    pass

@app.route("/login", methods=['POST'])
def log_in():
    #TODO: Change admin username
    data = request.get_json(force=True)
    username = data["username"]
    psw = data["password"]
    # Hash password to MD5

    result = db.get_admin()
    for res in result:
        if res[1] == psw:
            success = True
            break

    if success:
        token = find_token_of_admin(username)
        if token == None:
            token = generate_token(username)
        response = flask.Response(token)

    else:
        response = flask.Response("Failed")

    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

auths = {}

def generate_token(username):
    size = 15
    token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=size))
    auths[token] = username
    return token

def find_token_of_admin(username):
    for token, value in auths.keys():
            if value == username:
                return t.token
    return None

def auth_valid(token):
    if auths.count() > 0:
        for key, value in auths.keys():
            if key == token:
                return True
    else:
        return False

def message_callback(userid):
    # Get offset time (-1 == now)
    if offset == -1:
        offset = datetime.datetime.now()
    elif type(offset) is str:
        offset = datetime.datetime.strptime(offset, "%Y-%m-%d %H:%M:%S")

    # Filter messages that are > timestamp
    for message in messages:
        message = list(message)
        message[4] = datetime.datetime.strptime(message[4], "%Y-%m-%d %H:%M:%S")
        if message[4] < offset:
            filtered.append(message)

    temp = []

    if len(filtered) >= max_amount:
        for count in range(max_amount):
            temp.append({
                "msg_id": filtered[count][0],
                "user_name":  session.status[filtered[count][1]]["user_name"],
                "content": filtered[count][2],
                "direction": filtered[count][3],
                "timestamp": filtered[count][4].strftime("%Y-%m-%d %H:%M:%S"),
            })
    else:
        for message in filtered:
            temp.append({
                "msg_id": message[0],
                "user_name":  session.status[message[1]]["user_name"],
                "content": message[2],
                "direction": message[3],
                "timestamp": message[4].strftime("%Y-%m-%d %H:%M:%S"),
            })

    response = flask.Response(str(temp))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

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
    userid = event.source.user_id
    usermsg = event.message.text
    time = datetime.datetime.now()
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(time)

    # TODO: check timeout
    stat = session.get_status(userid)

    # Log user metadata
    print(f'User: {userid}')
    print(f'Message: {usermsg}')
    print(f'Status: {stat}\n')

    db.log(userid, usermsg, direction=0)
    session.status[userid]["last_msg"] = usermsg
    session.status[userid]["sess_time"] = time

    # User in registration
    if stat in ["r", "r0", "r1", "r2", "r_err"]:
        stat = e.registration(event, session)
        responder.registration_resp(event, stat, session)

    # User in scenario 1
    elif stat in ["s1s0", "s1s1", "s1d0", "s1d1", "s1d2", "s1d3", "s1d4", "s1d5", "s1d6", "s1s2", "s1s3", "s1s4"]:
        # Respond first then push...
        stat = e.high_temp(event, session)
        responder.high_temp_resp(userid, session, event)

    # TODO: User in scenario 2
    elif stat in ["s2s1", "s2s2", "s2s3"]:
        stat = e.push_news(userid, usermsg, session)
        responder.push_news_resp(event, session)

    # User trigger QA
    elif usermsg == '/qa':
        stat = 'qa0'
        session.switch_status(userid, stat)
        responder.qa_resp(event, session)

    elif stat in ["qa0", "qa1", "qa2_t", "qa2_f", "qa3"]:
        stat = e.qa(event, session)
        responder.qa_resp(event, session)

    '''
    (DEPRECATED) User in chat state (currently unable to communicate)
    '''
    # else:
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="不好意思，我還不會講話...")
    #     )
    #     db.log(userid, "不好意思，我還不會講話...", direction=1)

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
        StickerMessage(id=id,sticker_id=sticker_id,package_id=package_id)
    )
    pass

##############################
# Main function
##############################

if __name__ == "__main__":
    # Load session
    session.load_session()
    db.sync(session)

    client_status = {}

    # Hook interrupt signal
    signal.signal(signal.SIGINT, session.signal_handler)

    # Setup host port
    port = int(os.environ.get('PORT', 8080))
    # app.run(host='0.0.0.0', port=port, debug=True)
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
