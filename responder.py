# -*- coding: UTF-8 -*-
'''
The script for responding to user
- Registration
- TODO: Event High Temperature
- TODO: Event Push News
'''
# Import required modules
from linebot import (
        LineBotApi, WebhookHandler

)
from linebot.exceptions import (
        InvalidSignatureError

)
from linebot.models import (
        MessageEvent, TextMessage, TextSendMessage, StickerMessage

)

import utilities

##############################
# Application & variable initialization
##############################
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


def registration_resp(event, stat, session):
    '''
    Gets the status of user and replies according to user's registration status
    '''
    userid = event.source.user_id
    msg_r = {
        'r0': "請輸入您的姓名",
        'r1': "請輸入您的生日（年年年年月月日日）"
    }

    if stat == 'r0':
        msg = "初次見面，請輸入您的姓名"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    elif stat == 'r1':
        msg = "請輸入您的生日（年年年年月月日日）"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    elif stat == 'r2':
        msg = "註冊成功啦"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        session.status[userid]['sess_status'] = session.init_state
    elif stat == 'r_err':
        # TODO: Get last message for hint
        stat = session.status[userid]['sess_status']
        msg = "不好意思，您的輸入有所異常。\n" + msg_r[stat]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )

def qa_resp(event, stat, msg):
    # TODO
    if stat == 'qa0':
        msg = "您好，請問我可以如何幫你？"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    elif stat == 'qa1':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )

def high_temp_resp(event, stat):
    # TODO
    pass

def push_news_resp(event, stat):
    # TODO
    pass
