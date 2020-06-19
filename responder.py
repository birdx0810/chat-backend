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
from bert_serving.client import BertClient

import datetime
import pickle
import json
import traceback

import utilities
import environment
import database as db
import templates

##############################
# Application & variable initialization
##############################

keys = environment.get_key(environment.environment.get_env())
# Channel Access Token
line_bot_api = LineBotApi(keys[0])
# Channel Secret
handler = WebhookHandler(keys[1])

# Initialize BERT-as-service encoder
sentence_encoder = BertClient(ip='140.116.245.101')


def send_frontend(user_id, message, socketio, direction):
    try:
        frontend_data = json.dumps({
            "user_name": db.get_user_name(user_id),
            "user_id": user_id,
            "content": message,
            "direction": direction,
        })
        print("SOCKET: Sending to Front-End")
        socketio.emit('Message', frontend_data, json=True, broadcast=True)
        print("SOCKET: Emitted to Front-End")
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        print("Failed to emit message to frontend")


def send(user_id, message, socketio, event=None):
    '''
    This function wraps the utilties for logging and sending messages
    event == None:  Push messages
    '''
    try:
        if event is None:
            print("Event is None")
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=message)
            )
            print("Are you sleeping")
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
            )
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        print("Failed to send message to LINE")

    send_frontend(user_id, message, socketio, direction=1)

    # Save user message to DB (messages to user == 1)
    db.log(user_id, message, direction=1)


def send_template(user_id, template, socketio, event=None):
    '''
    This function wraps the utilties for logging and sending templates
    event == None:  Push templates
    '''
    try:
        if event is None:
            line_bot_api.push_message(
                user_id,
                template
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                template
            )
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        print("Failed to send message to LINE")

    send_frontend(user_id, template.alt_text, socketio, direction=1)

    db.log(user_id, template.alt_text, direction=1)


def registration_resp(event, status, socketio):
    '''
    Gets the status of user and replies according to user's registration status
    '''
    # Initialize variables
    user_id = event.source.user_id

    if status == 'r0':
        send(
            user_id=user_id,
            message=templates.registration_greeting,
            socketio=socketio,
            event=event
        )
    elif status == 'r1':
        send(
            user_id=user_id,
            message=templates.registration_birthday,
            socketio=socketio,
            event=event
        )
    elif status == 'r2':
        send(
            user_id=user_id,
            message=templates.registration_successful,
            socketio=socketio,
            event=event
        )
        db.update_status(user_id, "s")
    elif status == 'r_err':
        send(
            user_id=user_id,
            message=templates.registration_err(db.get_status(user_id)),
            socketio=socketio,
            event=event
        )


def qa_resp(event, status, socketio):
    '''
    Reply user according to status
    '''
    user_id = event.source.user_id
    text = event.message.text

    if status == "qa0":
        send(
            user_id=user_id,
            message=templates.qa_greeting,
            socketio=socketio,
            event=event
        )

    elif status == "qa1":
        found = False
        max_idx = 0
        text = text.lower()
        # Keyword matching
        for idx, qa in enumerate(templates.qa_list):
            for keyword in qa["keywords"]:
                if keyword in text:
                    found = True
                    max_idx = idx
                    break
            if found:
                break
        # Calculate cosine similarity if no keywords found in sentence
        if not found:
            query = sentence_encoder.encode([text])

            similarity = cosine_similarity(
                query,                          # 1 x Embedding
                templates.question_embeddings   # #Question x Embedding
            )[0]  # 1 x #Question
            max_idx = similarity.argmax()

        # Reply answer
        send(
            user_id=user_id,
            message=templates.qa_response(max_idx),
            socketio=socketio,
            event=event
        )

        send_template(
            user_id=user_id,
            template=templates.yn_template(templates.qa_check_is_helpful),
            socketio=socketio,
            event=None
        )

    elif status == "qa1_err":
        send(
            user_id=user_id,
            message=templates.qa_unknown,
            socketio=socketio,
            event=event
        )

        send_template(
            user_id=user_id,
            template=templates.yn_template(templates.qa_check_is_helpful),
            socketio=socketio,
            event=None
        )

    elif status == "qa2_t":

        send(
            user_id=user_id,
            message=templates.qa_thanks,
            socketio=socketio,
            event=event
        )

        db.update_status(user_id, "s")

    elif status == "qa2_f":
        send_template(
            user_id=user_id,
            template=templates.qa_template(),
            socketio=socketio,
            event=event
        )

    elif status == "qa3":
        msg = templates.qa_sorry

        for idx, qa in enumerate(templates.qa_list):
            if text == qa["question"]:
                msg = templates.qa_response(idx)
                break

        send(
            user_id=user_id,
            message=msg,
            socketio=socketio,
            event=event
        )
        send(
            user_id=user_id,
            message=templates.qa_thanks,
            socketio=socketio,
            event=None
        )
        db.update_status(user_id, "s")


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
        ask_status = templates.tf_template(msg)

        line_bot_api.push_message(user_id, ask_status)
        send(user_id=user_id, message=msg, socketio=socketio, event=False)

    # TODO: Status 1 - Ask if feeling sick
    elif status == 's1s1':
        # If true (not feeling well), ask for symptoms
        symptom_template = templates.symptoms_template()
        line_bot_api.reply_message(
            event.reply_token,
            symptom_template
        )
        send(user_id=user_id, message=symptom_template.alt_text,
             socketio=socketio, event=False)
    elif status == 's1f1':
        # If false (feeling ok), reply msg
        msg = "請持續密切留意您的您的體溫變化，多休息多喝水，至公共場合時記得戴口罩，至公共場合時記得戴口罩,若有任何身體不適仍建議您至醫療院所就醫。"
        session.switch_status(user_id, None)
        send(
            user_id=user_id,
            message=msg,
            socketio=socketio,
            event=event
        )

    # TODO: Status 2 - Ask for symptoms
    elif status == 's1d0' or status == 's1d1':
        # If '皮膚出疹' & '眼窩痛' detected
        msg = templates.symptom_reply[status]
        ask_clinic = templates.want_template(
            "為了您的安全健康，建議盡快至醫療院所就醫。\n是否需要提供您附近醫療院所的資訊？")

        send(
            user_id=user_id,
            message=msg,
            socketio=socketio,
            event=event
        )
        line_bot_api.push_message(
            user_id, TextSendMessage(templates.dengue_info()))
        send(user_id=user_id, message=templates.dengue_info(),
             socketio=socketio, event=False)

        line_bot_api.push_message(user_id, ask_clinic)
        send(user_id=user_id, message=ask_clinic.alt_text,
             socketio=socketio, event=False)

    elif status == 's1d2' or status == 's1d3' or status == 's1d4':
        # If '喉嚨痛' & '咳嗽' & '咳血痰' detected
        msg = templates.symptom_reply[status]
        ask_clinic = templates.want_template(
            "為了您的安全健康，建議盡快至醫療院所就醫。\n是否需要提供您附近醫療院所的資訊？")

        send(
            user_id=user_id,
            message=msg,
            socketio=socketio,
            event=event
        )
        line_bot_api.push_message(
            user_id, TextSendMessage(templates.flu_info()))
        send(user_id=user_id, message=templates.flu_info(),
             socketio=socketio, event=False)

        line_bot_api.push_message(user_id, ask_clinic)
        send(user_id=user_id, message=ask_clinic.alt_text,
             socketio=socketio, event=False)

    elif status == 's1d5':
        # If '肌肉酸痛' detected
        msg = templates.symptom_reply[status]
        ask_clinic = templates.want_template(
            "為了您的安全健康，建議盡快至醫療院所就醫。\n是否需要提供您附近醫療院所的資訊？")

        send(
            user_id=user_id,
            message=msg,
            socketio=socketio,
            event=event
        )

        info = templates.flu_info()+"\n"+templates.dengue_info()
        line_bot_api.push_message(user_id, TextSendMessage(info))
        send(user_id=user_id, message=info, socketio=socketio, event=False)

        line_bot_api.push_message(user_id, ask_clinic)
        send(user_id=user_id, message=ask_clinic.alt_text,
             socketio=socketio, event=False)

    elif status == 's1df':
        # If others
        msg = "請持續密切留意您的您的體溫變化，多休息多喝水，至公共場合時記得戴口罩，至公共場合時記得戴口罩,若有任何身體不適仍建議您至醫療院所就醫。"
        send(
            user_id=user_id,
            message=msg,
            socketio=socketio,
            event=event
        )
        session.switch_status(user_id, None)

    # Status 3: Ask for location
    elif status == 's1s2':
        # If replies to ask for nearby clinic
        msg = "請將您目前的位置傳送給我～"
        send(
            user_id=user_id,
            message=msg,
            socketio=socketio,
            event=event
        )

    elif status == 's1f2':
        # If doesn't need nearby clinic info
        msg = "請持續密切注意您的體溫變化，多休息多喝水，至公共場合時記得戴口罩，若有任何身體不適仍建議您至醫療院所就醫！"
        send(
            user_id=user_id,
            message=msg,
            socketio=socketio,
            event=event
        )
        session.switch_status(user_id, None)

    # TODO: Status 4: Return clinic and end scenario
    elif status == 's1s3':
        # Send clinic info and ask to go see doctor ASAP
        msg = "請盡快至您熟悉方便的醫療院所就醫。"
        clinic = templates.get_nearby_clinic(text)
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
        # TODO: push news and ask if not feeling well?
        # 1.1 Get news and templates message
        news = get_news()
        ask_location = templates.tf_template("請問您有在上述的區域內嗎？")
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
