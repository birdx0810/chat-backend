# -*- coding: UTF-8 -*-
# Import 3rd-Party Dependencies
from flask import (
    Flask, escape, request, redirect, url_for
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
import logging, signal, sys, os

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
is_development=True
if is_development:
    # Channel Access Token
    line_bot_api = LineBotApi('XEQclTuSIm6/pcNNB4W9a2DDX/KAbCBmZS4ltBl+g8q2IxwJyqdtgNNY9KtJJxfkuXbHmSdQPAqRWjAciP2IZgrvLoF3ZH2C2Hg+zZMgoy/xM/RbnoFa2eO9GV2F4E1qmjYxA0FbJm1uZkUms9o+4QdB04t89/1O/w1cDnyilFU=')
    # Channel Secret
    handler = WebhookHandler('fabfd7538c098fe222e8012e1df65740')
else:
    # Fill in when required
    pass

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

        print(f'User: {userid}')
        stat = 's1s0'
        session.switch_status(userid, stat)
        responder.high_temp_resp(userid, stat)
        return "OK"

@app.route("/api/event_push_news")
def push_news():
    #TODO: Trigger push_news
    pass

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

    # Log user metadata
    print(f'User: {userid}')
    print(f'Message: {usermsg}')

    # Check user status
    stat = session.get_status(userid)
    print(f'Status: {stat}')

    # User in registration
    if stat in ["r", "r0", "r1", "r2", "r_err"]:
        stat = e.registration(userid, usermsg, session)
        print(f'User: {userid}\nStatus Update: {stat}')
        responder.registration_resp(event, stat, session)

    # TODO: User in scenario 1
    elif stat in ["s1s1", "s1d1", "s1d2", "s1d3", "s1d4", "s1d5", "s1d6", "s1s2", "s1s3", "s1s4"]:
        # Respond first then push...
        stat = e.high_temp(userid, usermsg, session)
        responder.high_temp(event, stat, session)

    # TODO: User in scenario 2
    elif stat in ["s2s1", "s2s2", "s2s3"]:
        stat = e.push_news(userid, usermsg, session)
        responder.push_news(event, stat, session)

    # TODO: User trigger QA
    elif msg == '\qa':
        stat = 'qa0'
        session.switch_status(userid, stat)
        responder.qa_resp(event, stat, session)
    elif stat in ["qa0", "qa1", "qa2"]:
        stat = e.qa(userid, usermsg, session)
        responder.qa_resp(event, stat, session)

    # TODO: User in chat state (echo)
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text)
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

