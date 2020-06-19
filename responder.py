# -*- coding: UTF-8 -*-
'''
The script for responding to user according to status
- Registration
- QA
- Event High Temperature
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

from sklearn.metrics.pairwise import cosine_similarity

import datetime
import pickle
import json

import utilities
import environment
import database as db
import templates as t

##############################
# Application & variable initialization
##############################

keys = environment.get_key(environment.environment.get_env())
# Channel Access Token
line_bot_api = LineBotApi(keys[0])
# Channel Secret
handler = WebhookHandler(keys[1])

def send(user_id, message, socketio, event=None):
    '''
    This function wraps the utilties for logging and sending messages

    event == False: Do not send message (use when sending template), only use for emitting and logging to DB
    event == None:  Push messages
    '''
    #TODO: Try Catch

    if event == False:
        pass
    elif event is None:
        line_bot_api.push_message(user_id, message)
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
        )

    frontend_data = json.dumps({
        "user_name": db.get_user_name(user_id),
        "user_id": user_id,
        "content": message,
        "direction": 1,
    })

    print("SOCKET: Sending to Front-End")
    socketio.emit('Message', frontend_data, json=True, broadcast=True)
    print("SOCKET: Emitted to Front-End")

    db.log(user_id, message, direction=1)    # Save user message to DB (messages to user == 1)

def registration_resp(event, status, socketio):
    '''
    Gets the status of user and replies according to user's registration status
    '''
    # Initialize variables
    user_id = event.source.user_id

    err_msg = {
        'r0': "請輸入您的中文姓名（e.g. 大鳥陳）",
        'r1': "請輸入您的生日（年年年年月月日日）"
    }

    if status == 'r0':
        msg = "初次見面，請輸入您的中文姓名"
        send(user_id=user_id, message=msg, socketio=socketio, event=event)
    elif status == 'r1':
        msg = "請輸入您的生日（年年年年月月日日）"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        db.log(user_id, msg, direction=1)
        # send(user_id=user_id, message=msg, socketio=socketio, event=event)
    elif status == 'r2':
        msg = "註冊成功啦"
        send(user_id=user_id, message=msg, socketio=socketio, event=event)
        session.status[user_id]['sess_status'] = session.init_state
    elif status == 'r_err':
        msg = "不好意思，您的輸入有所異常。\n" + err_msg[db.get_status(user_id)]
        send(user_id=user_id, message=msg, socketio=socketio, event=event)

def qa_resp(event, session, socketio):
    '''
    Reply user according to status
    '''
    user_id = event.source.user_id
    text = event.message.text
    status = session.status[user_id]['sess_status']

    # Initialize BERT-as-service encoder
    from bert_serving.client import BertClient
    bc = BertClient(ip='140.116.245.101')

    if status == 'qa0':
        msg = "你好，請問我可以如何幫你？\n(小弟目前還在學習中，請多多指教～"
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=msg)
        # )
        send(user_id=user_id, message=msg, socketio=socketio, event=event)

    elif status == 'qa1':
        found = False
        # Keyword matching
        for keys, values in t.qa_dict.items():
            for keyword in keys:
                if keyword in text.lower():
                    found = True
                    msg = f"你想問的問題可能是:\n`{values[0]}`\n\n我們的回答是:`{values[1]}`"
        # Calculate cosine similarity if no keywords found in sentence
        if found == False:
            query = bc.encode([text])
            similarity = []
            for idx in range(len(t.question_embeddings)):
                query = query.transpose()
                sim = cosine_similarity(query, t.question_embeddings[idx].resize((768,1)))
                similarity.append(sim)
            max_idx, _ = max((i,v)for i,v in enumerate(similarity))
            msg = f"你想問的問題可能是:\n`{values[0]}`\n\n我們的回答是:\n`{values[1]}`"
        # Reply answer
        is_correct = t.yn_template('請問是否是你想要問的問題嗎？')
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=msg)
        # )
        send(user_id=user_id, message=msg, socketio=socketio, event=event)
        line_bot_api.push_message(user_id, is_correct)
        send(user_id=user_id, message=is_correct.alt_text, socketio=socketio, event=False)

    elif status == 'qa1_err':
        msg = '不好意思，我不明白你的意思…'
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=msg)
        # )
        send(user_id=user_id, message=msg, socketio=socketio, event=event)
        pass

    elif status == 'qa2_t':
        msg = "感謝你的回饋。很高興可以幫到你～"
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=msg)
        # )
        send(user_id=user_id, message=msg, socketio=socketio, event=event)
        session.switch_status(user_id, None)

    elif status == 'qa2_f':
        qa_labels = t.qa_labels()
        line_bot_api.reply_message(
            event.reply_token,
            qa_labels
        )
        # send(user_id=user_id, message=qa_labels, socketio=socketio, event=event)

    elif status == 'qa3':
        for keys, values in t.qa_dict.items():
            if text == values[0]:
                msg = f"你想問的問題可能是:\n`{values[0]}`\n\n我們的回答是:\n`{values[1]}`\n\n感謝您的回饋。"
                break
            else:
                msg = f"不好意思，目前沒辦法回應你的需求。我們會再改進～"
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=msg)
        # )
        send(user_id=user_id, message=msg, socketio=socketio, event=event)
        session.switch_status(user_id, None)

def high_temp_resp(user_id, session, socketio, event=None):
    '''
    High temperature event responder
    '''
    # Initialize variables
    if event is not None:
        text = event.message.text
    status = session.status[user_id]['sess_status']

    # Scene 1:
    # Status 0 - API triggered
    if status == 's1s0':
        # Detected user high temperature, ask patient well being
        msg = "您好，手環資料顯示您的體溫似乎比較高，請問您有不舒服的情形嗎？"
        ask_status = t.tf_template(msg)

        line_bot_api.push_message(user_id, ask_status)
        send(user_id=user_id, message=msg, socketio=socketio, event=False)

    # TODO: Status 1 - Ask if feeling sick
    elif status == 's1s1':
        # If true (not feeling well), ask for symptoms
        symptom_template = t.symptoms_template()
        line_bot_api.reply_message(
            event.reply_token,
            symptom_template
        )
        send(user_id=user_id, message=symptom_template.alt_text, socketio=socketio, event=False)
    elif status == 's1f1':
        # If false (feeling ok), reply msg
        msg = "請持續密切留意您的您的體溫變化，多休息多喝水，至公共場合時記得戴口罩，至公共場合時記得戴口罩,若有任何身體不適仍建議您至醫療院所就醫。"
        session.switch_status(user_id, None)
        send(user_id=user_id, message=msg, socketio=socketio, event=event)

    # TODO: Status 2 - Ask for symptoms
    elif status == 's1d0' or status == 's1d1':
        # If '皮膚出疹' & '眼窩痛' detected
        msg = t.symptom_reply[status]
        ask_clinic = t.want_template("為了您的安全健康，建議盡快至醫療院所就醫。\n是否需要提供您附近醫療院所的資訊？")

        send(user_id=user_id, message=msg, socketio=socketio, event=event)
        line_bot_api.push_message(user_id, TextSendMessage(t.dengue_info()))
        send(user_id=user_id, message=t.dengue_info(), socketio=socketio, event=False)

        line_bot_api.push_message(user_id, ask_clinic)
        send(user_id=user_id, message=ask_clinic.alt_text, socketio=socketio, event=False)

    elif status == 's1d2' or status == 's1d3' or status == 's1d4':
        # If '喉嚨痛' & '咳嗽' & '咳血痰' detected
        msg = t.symptom_reply[status]
        ask_clinic = t.want_template("為了您的安全健康，建議盡快至醫療院所就醫。\n是否需要提供您附近醫療院所的資訊？")

        send(user_id=user_id, message=msg, socketio=socketio, event=event)
        line_bot_api.push_message(user_id, TextSendMessage(t.flu_info()))
        send(user_id=user_id, message=t.flu_info(), socketio=socketio, event=False)

        line_bot_api.push_message(user_id, ask_clinic)
        send(user_id=user_id, message=ask_clinic.alt_text, socketio=socketio, event=False)


    elif status == 's1d5':
        # If '肌肉酸痛' detected
        msg = t.symptom_reply[status]
        ask_clinic = t.want_template("為了您的安全健康，建議盡快至醫療院所就醫。\n是否需要提供您附近醫療院所的資訊？")

        send(user_id=user_id, message=msg, socketio=socketio, event=event)

        info = t.flu_info()+"\n"+t.dengue_info()
        line_bot_api.push_message(user_id, TextSendMessage(info))
        send(user_id=user_id, message=info, socketio=socketio, event=False)

        line_bot_api.push_message(user_id, ask_clinic)
        send(user_id=user_id, message=ask_clinic.alt_text, socketio=socketio, event=False)

    elif status == 's1df':
        # If others
        msg = "請持續密切留意您的您的體溫變化，多休息多喝水，至公共場合時記得戴口罩，至公共場合時記得戴口罩,若有任何身體不適仍建議您至醫療院所就醫。"
        send(user_id=user_id, message=msg, socketio=socketio, event=event)
        session.switch_status(user_id, None)

    # Status 3: Ask for location
    elif status == 's1s2':
        # If replies to ask for nearby clinic
        msg = "請將您目前的位置傳送給我～"
        send(user_id=user_id, message=msg, socketio=socketio, event=event)

    elif status == 's1f2':
        # If doesn't need nearby clinic info
        msg = "請持續密切注意您的體溫變化，多休息多喝水，至公共場合時記得戴口罩，若有任何身體不適仍建議您至醫療院所就醫！"
        send(user_id=user_id, message=msg, socketio=socketio, event=event)
        session.switch_status(user_id, None)

    # TODO: Status 4: Return clinic and end scenario
    elif status == 's1s3':
        # Send clinic info and ask to go see doctor ASAP
        msg =  "請盡快至您熟悉方便的醫療院所就醫。"
        clinic = t.get_nearby_clinic(text)
        line_bot_api.reply_message(
            event.reply_token,
            clinic
        )
        line_bot_api.push_message(user_id, TextSendMessage(text=msg))
        send(user_id=user_id, message=msg, socketio=socketio, event=False)
        session.switch_status(user_id, None)
        pass

def push_news_resp(event, session):
    # TODO: Push medical related news to all users
    # Initialize variables
    user_id = event.source.user_id
    status = session.status[user_id]['sess_status']

    if status == 's2s0':
        #TODO: push news and ask if not feeling well?
        # 1.1 Get news and template message
        news = get_news()
        ask_location = t.tf_template("請問您有在上述的區域內嗎？")
        # 1.2 Push news and ask if in location
        line_bot_api.push_message(user_id, news)
        line_bot_api.push_message(user_id, ask_location)
    elif status == 's2s1':
        # 2.1 If in location with case
        msg = "因為您所在的地區有確診案例，請問您有不舒服的狀況嗎？"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    elif status == 's2f1':
        # 2.2 If not in the location (end)
        msg = "您所在的位置非疫情區，因此不用太過緊張。若有最新消息將會立即更新讓您第一時間了解！"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    elif status == 's2s2':
        # 2.3 Doctor function
        msg = "把我當成一個醫生，說說您現在哪邊不舒服？"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    pass
