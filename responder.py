# -*- coding: UTF-8 -*-
"""
The script for responding to user according to status
- Registration
- QA
- Event High Temperature
- TODO: Event Push News
"""

import json
import traceback

# Import required modules
from linebot import (
    LineBotApi, WebhookHandler
)

from linebot.models import (
    TextSendMessage, LocationSendMessage
)

from sklearn.metrics.pairwise import cosine_similarity
from bert_serving.client import BertClient

import environment
import database as db
import templates

##############################
# Application & variable initialization
##############################

keys = environment.get_key()
# Channel Access Token
line_bot_api = LineBotApi(keys[0])
# Channel Secret
handler = WebhookHandler(keys[1])


def send_frontend(direction=None, message=None, socketio=None, timestamp=None, user_id=None):
    try:
        frontend_data = json.dumps([{
            "user_name": db.get_user_name(user_id=user_id),
            "user_id": user_id,
            "content": message,
            "direction": direction,
            "timestamp": timestamp
        }])
        print("SOCKET: Sending to Front-End")
        socketio.emit("Message", frontend_data, json=True, broadcast=True)
        print("SOCKET: Emitted to Front-End")
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        print("Failed to emit message to frontend")


def send_text(event=None, message=None, socketio=None, user_id=None):
    """
    This function wraps the utilties for logging and sending messages
    event is None:  Push messages
    """
    # Save user message to DB (messages to user == 1)
    timestamp, _, _ = db.log(
        direction=1,
        message=message,
        user_id=user_id
    )

    try:
        if event is None:
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=message)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
            )
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        print("Failed to send message to LINE")

    send_frontend(
        direction=1,
        message=message,
        socketio=socketio,
        timestamp=timestamp,
        user_id=user_id
    )


def send_template(event=None, socketio=None, template=None, user_id=None):
    """
    This function wraps the utilties for logging and sending templates
    event is None:  Push templates
    """

    # Save user message to DB (messages to user == 1)
    timestamp, _, _ = db.log(
        direction=1,
        message=template.alt_text,
        user_id=user_id
    )

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
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        print("Failed to send message to LINE")

    send_frontend(
        direction=1,
        message=template.alt_text,
        socketio=socketio,
        timestamp=timestamp,
        user_id=user_id
    )


def send_location(event=None, location=None, socketio=None, user_id=None):
    # Save user message to DB (messages to user == 1)
    timestamp, _, _ = db.log(
        direction=1,
        message=location.title + "\n" + location.address,
        user_id=user_id
    )

    try:
        if event is None:
            line_bot_api.push_message(
                user_id,
                location
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                location
            )
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        print("Failed to send message to LINE")

    send_frontend(
        direction=1,
        message=location.title + "\n" + location.address,
        socketio=socketio,
        timestamp=timestamp,
        user_id=user_id
    )


def registration(event=None, socketio=None, status=None):
    """
    Gets the status of user and replies according to user's registration status
    """
    # Initialize variables
    user_id = event.source.user_id

    if status == "r0":
        send_text(
            event=event,
            message=templates.registration_greeting,
            socketio=socketio,
            user_id=user_id
        )
    elif status == "r1":
        send_text(
            event=event,
            message=templates.registration_birthday,
            socketio=socketio,
            user_id=user_id
        )
    elif status == "r2":
        send_text(
            event=event,
            message=templates.registration_successful,
            socketio=socketio,
            user_id=user_id
        )
        db.update_status(status="s", user_id=user_id)
    elif status == "r_err":
        send_text(
            event=event,
            message=templates.registration_err(
                status=db.get_status(user_id=user_id)
            ),
            socketio=socketio,
            user_id=user_id
        )
    else:
        raise ValueError(f"Invalid status: {status}")


def qa(event=None, message=None, socketio=None, status=None):
    """
    Reply user according to status
    """
    user_id = event.source.user_id

    if status == "qa0":
        send_text(
            event=event,
            message=templates.qa_greeting,
            socketio=socketio,
            user_id=user_id
        )

    elif status == "qa1":
        found = False
        max_idx = 0
        message = message.lower()
        # Keyword matching
        for idx, qa_obj in enumerate(templates.qa_list):
            for keyword in qa_obj["keywords"]:
                if keyword in message:
                    found = True
                    max_idx = idx
                    break
            if found:
                break

        # Reply answer
        send_text(
            event=event,
            message=templates.qa_response(max_idx),
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            socketio=socketio,
            template=templates.yn_template(templates.qa_check_is_helpful),
            user_id=user_id
        )

    elif status == "qa1_err":
        send_text(
            event=event,
            message=templates.qa_unknown,
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            socketio=socketio,
            template=templates.yn_template(templates.qa_check_is_helpful),
            user_id=user_id
        )

    elif status == "qa2_t":

        send_text(
            event=event,
            message=templates.qa_thanks,
            socketio=socketio,
            user_id=user_id
        )

        db.update_status(status="s", user_id=user_id)

    elif status == "qa2_f":
        send_template(
            event=event,
            socketio=socketio,
            template=templates.qa_template(),
            user_id=user_id
        )

    elif status == "qa2_err":
        send_text(
            event=event,
            message=templates.qa_unknown,
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            socketio=socketio,
            template=templates.qa_template(),
            user_id=user_id
        )

    elif status == "qa3":
        response_msg = templates.qa_sorry

        for idx, qa_obj in enumerate(templates.qa_list):
            if message == qa_obj["question"]:
                response_msg = templates.qa_response(idx)
                break

        send_text(
            event=event,
            message=response_msg,
            socketio=socketio,
            user_id=user_id
        )
        send_text(
            event=None,
            message=templates.qa_thanks,
            socketio=socketio,
            user_id=user_id
        )
        db.update_status(status="s", user_id=user_id)
    else:
        raise ValueError(f"Invalid status: {status}")


def high_temp(event=None, message=None, socketio=None, status=None, user_id=None):
    """
    High temperature event responder
    """

    # Scene 1:
    # Status 0 - API triggered
    if status == "s1s0":
        # Detected user high temperature, ask patient well being
        send_template(
            event=None,
            template=templates.tf_template(templates.high_temp_greeting),
            socketio=socketio,
            user_id=user_id
        )

    # Status 1 - Ask if feeling sick
    elif status == "s1s1":
        # If true (not feeling well), ask for symptoms
        send_template(
            event=None,
            template=templates.symptoms_template(),
            socketio=socketio,
            user_id=user_id
        )

    elif status == "s1f1":
        # If false (feeling ok), reply msg
        send_text(
            event=event,
            message=templates.high_temp_ending,
            socketio=socketio,
            user_id=user_id
        )

        db.update_status(status="s", user_id=user_id)

    elif status == "s1s0_err":
        send_text(
            event=event,
            message=templates.high_temp_unknown,
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            template=templates.tf_template(templates.high_temp_greeting),
            socketio=socketio,
            user_id=user_id
        )

    # Status 2 - Ask for symptoms
    elif status in ["s1d0", "s1d1"]:
        # If "皮膚出疹" & "眼窩痛" detected
        send_text(
            event=event,
            message=list(filter(
                lambda symptom: symptom["status"] == status, templates.symptoms_list
            ))[0]["reply"],
            socketio=socketio,
            user_id=user_id
        )

        send_text(
            event=None,
            message=templates.dengue_info(),
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            template=templates.yn_template(templates.high_temp_ask_clinic),
            socketio=socketio,
            user_id=user_id
        )

    elif status in ["s1d2", "s1d3", "s1d4"]:
        # If "喉嚨痛" & "咳嗽" & "咳血痰" detected
        send_text(
            event=event,
            message=list(filter(
                lambda symptom: symptom["status"] == status, templates.symptoms_list
            ))[0]["reply"],
            socketio=socketio,
            user_id=user_id
        )

        send_text(
            event=None,
            message=templates.flu_info(),
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            template=templates.yn_template(templates.high_temp_ask_clinic),
            socketio=socketio,
            user_id=user_id
        )

    elif status == "s1d5":
        # If "肌肉酸痛" detected
        send_text(
            event=event,
            message=list(filter(
                lambda symptom: symptom["status"] == status, templates.symptoms_list
            ))[0]["reply"],
            socketio=socketio,
            user_id=user_id
        )

        send_text(
            event=None,
            message=templates.flu_info()+"\n"+templates.dengue_info(),
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            template=templates.yn_template(templates.high_temp_ask_clinic),
            socketio=socketio,
            user_id=user_id
        )

    elif status == "s1df":
        # If other or no symptoms
        send_text(
            event=event,
            message=templates.high_temp_unknown,
            socketio=socketio,
            user_id=user_id
        )

        send_text(
            event=None,
            message=templates.high_temp_ending,
            socketio=socketio,
            user_id=user_id
        )

        db.update_status(status="s", user_id=user_id)

    # Status 3: Ask for location
    elif status == "s1s2":
        # If replies to ask for nearby clinic
        send_text(
            event=event,
            message=templates.high_temp_ask_location,
            socketio=socketio,
            user_id=user_id
        )

    elif status == "s1f2":
        # If doesn't need nearby clinic info
        send_text(
            event=event,
            message=templates.high_temp_ending,
            socketio=socketio,
            user_id=user_id
        )
        db.update_status(status="s", user_id=user_id)

    elif status == "s1dx_err":
        send_text(
            event=event,
            message=templates.high_temp_unknown,
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            template=templates.yn_template(templates.high_temp_ask_clinic),
            socketio=socketio,
            user_id=user_id
        )

    # Status 4: Return clinic and end scenario
    elif status == "s1s3":
        # Send clinic info and ask to go see doctor ASAP
        clinic = templates.get_nearby_clinic(message)

        if isinstance(clinic, LocationSendMessage):
            send_location(
                event=event,
                location=clinic,
                socketio=socketio,
                user_id=user_id
            )
        else:
            send_text(
                event=event,
                message=clinic,
                socketio=socketio,
                user_id=user_id
            )

        db.update_status(status="s", user_id=user_id)


def wait(event=None, message=None, socketio=None, status=None, user_id=None):

    send_text(
        event=event,
        message=templates.system_wait_admin,
        socketio=socketio,
        user_id=user_id
    )
