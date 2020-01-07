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
import db, session

# Initialize Flask
app = Flask(__name__)

# Initialize Session
session = session.Session()

# Channel API & Webhook
line_bot_api = LineBotApi('ziOmFT6dChd1K/l4IlRUfe37gYQ9aFiLHsnKi/ukJr5UDcqzh7bgU/i8MBqrqULyuXbHmSdQPAqRWjAciP2IZgrvLoF3ZH2C2Hg+zZMgoy/4W0Ahb7g7l9T7AbQqlNqsVFCJHSCyHOJH6HBT5ccxAgdB04t89/1O/w1cDnyilFU=') # Channel Access Token
handler = WebhookHandler('fabfd7538c098fe222e8012e1df65740') # Channel Secret

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

    print(f'User status:{session.status}')

    # Check user status
    stat = db.check_user(userid, usermsg, session)

    # Registration reply
    if stat == 'r0':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="初次見面，請輸入您的姓名")
        )
    elif stat == 'r1':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入您的生日（年年年年月月日日）")
        )
    elif stat == 'r2':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入您的身份證末四碼")
        )
    elif stat == 'r3':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="註冊成功啦")
        )
        session.status[userid]['sess_status'] = session.init_state
    elif stat == 'error':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="不好意思，您的輸入有所異常。請重新輸入…")
        )
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
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

