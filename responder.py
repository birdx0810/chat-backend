# -*- coding: UTF-8 -*-
# Log final message
def final_msg():
    session.status[userid]['sess_status'] = session.init_state

# Registration reply module
def registration(event, stat)
    '''
    Gets the status of user and replies according to user's registration status
    '''
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
    elif stat == 'error':
        msg = "不好意思，您的輸入有所異常。請重新輸入…"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
