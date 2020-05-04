# -*- coding: UTF-8 -*-
# Import 3rd-Party Dependencies
from flask import (
    Flask, abort, escape, request, redirect, url_for, jsonify
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
import json

# Import local modules
import database as db
import event as e
import utilities, responder

##############################
# Application & variable initialization
##############################
# Initialize Flask
app = Flask(__name__)

# Is development or production
is_development=False
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

@app.route("/backend_api/users", methods=['POST'])
def get_user():
    #TODO: Verify request from backend
    users = db.get_users()
    return jsonify(users)

@app.route("/backend_api/messages", methods=['POST'])
def get_msgs():
    #TODO: Verify request from backend
    messages = db.get_messages()
    return jsonify(messages)

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

    # TODO: check timeout
    stat = session.get_status(userid)

    # Log user metadata
    print(f'User: {userid}')
    print(f'Message: {usermsg}')
    print(f'Status: {stat}\n')

    # User in registration
    if stat in ["r", "r0", "r1", "r2", "r_err"]:
        stat = e.registration(event, session)
        responder.registration_resp(event, stat, session)

    # TODO: User in scenario 1
    elif stat in ["s1s0", "s1s1", "s1d0", "s1d1", "s1d2", "s1d3", "s1d4", "s1d5", "s1d6", "s1s2", "s1s3", "s1s4"]:
        # Respond first then push...
        stat = e.high_temp(event, session)
        responder.high_temp_resp(userid, session, event)

    # TODO: User in scenario 2
    elif stat in ["s2s1", "s2s2", "s2s3"]:
        stat = e.push_news(userid, usermsg, session)
        responder.push_news_resp(event, session)

    # TODO: User trigger QA
    elif usermsg == '/qa':
        stat = 'qa0'
        session.switch_status(userid, stat)
        responder.qa_resp(event, session)

    elif stat in ["qa0", "qa1", "qa2_t", "qa2_f", "qa3"]:
        stat = e.qa(event, session)
        responder.qa_resp(event, session)

    # TODO: User in chat state (unable to communicate)
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="不好意思，我還不會講話...")
        )

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

    # Hook interrupt signal
    signal.signal(signal.SIGINT, session.signal_handler)

    # Setup host port
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

    # Call function at apointed time
    while True:
        time.sleep(3600*30)
        time = datetime.datetime.now().strftime("%H:%M")
        if time == "00:00":
            db.sync(session)
        # if time == 20:00:
            # TODO: Run news crawler
            # got_news = crawl()
        # if got_news:
            # TODO: Call news API
        # break
