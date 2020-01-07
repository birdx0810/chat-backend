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
import sys, os

# Import local modules
import database, session, utilities, responder

# Initialize Flask
app = Flask(__name__)

# Initialize Session
session = session.Session()

# Channel Access Token
line_bot_api = LineBotApi('XEQclTuSIm6/pcNNB4W9a2DDX/KAbCBmZS4ltBl+g8q2IxwJyqdtgNNY9KtJJxfkuXbHmSdQPAqRWjAciP2IZgrvLoF3ZH2C2Hg+zZMgoy/xM/RbnoFa2eO9GV2F4E1qmjYxA0FbJm1uZkUms9o+4QdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('fabfd7538c098fe222e8012e1df65740') 

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

# Text message handler
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
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
    print(f'Status:{stat}')

    # User in registration
    if stat in ["r0", "r1", "r2", "r_err"]:
        stat = utilities.register(userid, usermsg, session)
        responder.registration(event, stat)
        pass
    else:
    # Reply user
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text)
        )

# Sticker message handler (echo)
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

if __name__ == "__main__":
    signal.signal(signal.SIGINT, sess.signal_handler)
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

