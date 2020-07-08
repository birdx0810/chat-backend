# -*- coding: UTF-8 -*-
"""
The script for responding to user according to status
- Registration
- QA
- Event High Temperature
- TODO: Event Push News
"""

from urllib.parse import urlparse
from datetime import timedelta, datetime
import json
import math
import traceback

# Import required modules
from linebot import (
    LineBotApi, WebhookHandler
)

from linebot.models import (
    TextSendMessage, LocationSendMessage
)

from pywebpush import webpush, WebPushException

import environment
import database as db
import similarity
import templates
import status_code

##############################
# Application & variable initialization
##############################

keys = environment.get_key()
# Channel Access Token
line_bot_api = LineBotApi(keys[0])
# Channel Secret
handler = WebhookHandler(keys[1])


def send_frontend(
        direction=None,
        message=None,
        require_read=False,
        socketio=None,
        timestamp=None,
        user_id=None
    ):

    try:
        frontend_data = json.dumps([{
            "content": message,
            "direction": direction,
            "require_read": require_read,
            "timestamp": timestamp,
            "user_id": user_id,
            "user_name": db.get_user_name(user_id=user_id),
        }])
        print("SOCKET: Sending to Front-End")
        socketio.emit("Message", frontend_data, json=True, broadcast=True)
        print("SOCKET: Emitted to Front-End")
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        print("Failed to emit message to frontend")


def send_text(
        event=None,
        message=None,
        require_read=False,
        socketio=None,
        user_id=None
    ):
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

    if require_read:
        db.message_require_read(user_id=user_id)
        push_notification(message=message, user_id=user_id)

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
        require_read=require_read,
        socketio=socketio,
        timestamp=timestamp,
        user_id=user_id
    )


def send_template(event=None, socketio=None, template=None, user_id=None):
    """
    This function wraps the utilties for logging and sending templates
    event is None: Push templates
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


def push_notification(user_id=None, message=None):
    try:
        admins = db.get_push_info()
        message = templates.system_notification_message(
            user_name=db.get_user_name(user_id=user_id)
        )
        for admin in admins:
            try:
                endpoint = urlparse(admin["endpoint"])
                endpoint_origin = '{uri.scheme}://{uri.netloc}'.format(
                    uri=endpoint)
                webpush(
                    subscription_info={
                        "endpoint": admin["endpoint"],
                        "keys": {
                            "auth": admin["auth"],
                            "p256dh": admin["p256dh"],
                        }
                    },
                    data=message,
                    vapid_private_key=environment.get_vapid_key()[1],
                    vapid_claims={
                        "sub": "mailto:bird@example.org",
                        "aud": endpoint_origin,
                        "exp": math.floor(
                            datetime.now().timestamp() + timedelta(days=1).total_seconds()
                        )
                    }
                )

            except WebPushException as err:
                print(err)
                print(traceback.format_exc())
                print("Failed to push notification")

    except Exception as err:
        print(err)
        print(traceback.format_exc())
        print("Failed to push notification")


def registration(event=None, socketio=None, status=None):
    """
    Gets the status of user and replies according to user's registration status
    """
    # Initialize variables
    user_id = event.source.user_id

    if status == status_code.registration["ask_user_name"]:
        send_text(
            event=event,
            message=templates.registration_greeting,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )
    elif status == status_code.registration["ask_birth_day"]:
        send_text(
            event=event,
            message=templates.registration_birthday,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )
    elif status == status_code.registration["end"]:
        send_text(
            event=event,
            message=templates.registration_successful,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )
        db.update_status(
            status=status_code.system["null_state"], user_id=user_id)
    elif status == status_code.registration["error"]:
        send_text(
            event=event,
            message=templates.registration_err(
                status=db.get_status(user_id=user_id)
            ),
            require_read=False,
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

    if status == status_code.qa["initialization"]:
        send_text(
            event=event,
            message=templates.qa_greeting,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

    elif status == status_code.qa["received_question"]:

        max_idx = similarity.question(message)

        if max_idx is not None:
            # Found question and reply answer
            send_text(
                event=event,
                message=templates.qa_response(max_idx),
                require_read=False,
                socketio=socketio,
                user_id=user_id
            )

            send_template(
                event=None,
                socketio=socketio,
                template=templates.yn_template(templates.qa_check_is_helpful),
                user_id=user_id
            )

            db.update_status(
                status=status_code.qa["found_question"], user_id=user_id)
        else:
            # Question not found, ask if need customer service
            send_text(
                event=event,
                message=templates.qa_sorry,
                require_read=False,
                socketio=socketio,
                user_id=user_id
            )

            send_template(
                event=None,
                socketio=socketio,
                template=templates.yn_template(
                    templates.qa_check_custom_service),
                user_id=user_id
            )

            db.update_status(
                status=status_code.qa["fail_to_find_question"], user_id=user_id)

    elif status == status_code.qa["found_unknown"]:
        send_text(
            event=event,
            message=templates.qa_unknown,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            socketio=socketio,
            template=templates.yn_template(templates.qa_check_is_helpful),
            user_id=user_id
        )

    elif status == status_code.qa["not_found_unknown"]:
        send_text(
            event=event,
            message=templates.qa_unknown,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            socketio=socketio,
            template=templates.yn_template(templates.qa_check_custom_service),
            user_id=user_id
        )

    elif status == status_code.qa["is_correct_question"]:

        send_text(
            event=event,
            message=templates.qa_thanks,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        db.update_status(
            status=status_code.system["null_state"], user_id=user_id)

    elif status == status_code.qa["not_correct_question"]:
        send_template(
            event=event,
            socketio=socketio,
            template=templates.qa_template(),
            user_id=user_id
        )

    elif status == status_code.qa["label_unknown"]:
        send_text(
            event=event,
            message=templates.qa_unknown,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            socketio=socketio,
            template=templates.qa_template(),
            user_id=user_id
        )

    elif status == status_code.qa["user_label_answer"]:
        response_msg = templates.qa_sorry

        for idx, qa_obj in enumerate(templates.qa_list):
            if message == qa_obj["question"]:
                response_msg = templates.qa_response(idx)
                break

        send_text(
            event=event,
            message=response_msg,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )
        send_text(
            event=None,
            message=templates.qa_thanks,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )
        db.update_status(
            status=status_code.system["null_state"], user_id=user_id)

    elif status == status_code.qa["contact_customer_service"]:
        send_text(
            event=event,
            message=templates.system_wait_admin,
            require_read=True,
            socketio=socketio,
            user_id=user_id
        )

        db.update_status(
            status=status_code.system["wait_customer_service"], user_id=user_id)
    else:
        raise ValueError(f"Invalid status: {status}")


def high_temp(event=None, message=None, socketio=None, status=None, user_id=None):
    """
    High temperature event responder
    """

    # Scene 1:
    # Status 0 - API triggered
    if status == status_code.high_temp["initialization"]:
        # Detected user high temperature, ask patient well being
        send_template(
            event=None,
            template=templates.tf_template(templates.high_temp_greeting),
            socketio=socketio,
            user_id=user_id
        )

    # Status 1 - Ask if feeling sick
    elif status == status_code.high_temp["user_not_feeling_well"]:
        # If true (not feeling well), ask for symptoms
        send_template(
            event=None,
            template=templates.symptoms_template(),
            socketio=socketio,
            user_id=user_id
        )

    elif status == status_code.high_temp["user_feeling_well"]:
        # If false (feeling ok), reply msg
        send_text(
            event=event,
            message=templates.high_temp_ending,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        db.update_status(
            status=status_code.system["null_state"], user_id=user_id)

    elif status == status_code.high_temp["user_feeling_unknown"]:
        send_text(
            event=event,
            message=templates.high_temp_unknown,
            require_read=False,
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
    elif status in [
            status_code.high_temp["皮膚出疹"],
            status_code.high_temp["眼窩痛"]
    ]:
        # If "皮膚出疹" & "眼窩痛" detected
        send_text(
            event=event,
            message=list(filter(
                lambda symptom: symptom["status"] == status, templates.symptoms_list
            ))[0]["reply"],
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        send_text(
            event=None,
            message=templates.dengue_info(),
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            template=templates.yn_template(templates.high_temp_ask_clinic),
            socketio=socketio,
            user_id=user_id
        )

    elif status in [
            status_code.high_temp["喉嚨痛"],
            status_code.high_temp["咳嗽"],
            status_code.high_temp["咳血痰"],
    ]:
        # If "喉嚨痛" & "咳嗽" & "咳血痰" detected
        send_text(
            event=event,
            message=list(filter(
                lambda symptom: symptom["status"] == status, templates.symptoms_list
            ))[0]["reply"],
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        send_text(
            event=None,
            message=templates.flu_info(),
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            template=templates.yn_template(templates.high_temp_ask_clinic),
            socketio=socketio,
            user_id=user_id
        )

    elif status == status_code.high_temp["肌肉酸痛"]:
        # If "肌肉酸痛" detected
        send_text(
            event=event,
            message=list(filter(
                lambda symptom: symptom["status"] == status, templates.symptoms_list
            ))[0]["reply"],
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        send_text(
            event=None,
            message=templates.flu_info()+"\n"+templates.dengue_info(),
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        send_template(
            event=None,
            template=templates.yn_template(templates.high_temp_ask_clinic),
            socketio=socketio,
            user_id=user_id
        )

    elif status == status_code.high_temp["other_symptom"]:
        # If other or no symptoms
        send_text(
            event=event,
            message=templates.high_temp_unknown,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        send_text(
            event=None,
            message=templates.high_temp_ending,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

        db.update_status(
            status=status_code.system["null_state"], user_id=user_id)

    # Status 3: Ask for location
    elif status == status_code.high_temp["need_clinic_info"]:
        # If replies to ask for nearby clinic
        send_text(
            event=event,
            message=templates.high_temp_ask_location,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )

    elif status == status_code.high_temp["dont_need_clinic_info"]:
        # If doesn't need nearby clinic info
        send_text(
            event=event,
            message=templates.high_temp_asap,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )
        db.update_status(
            status=status_code.system["null_state"], user_id=user_id)

    elif status == status_code.high_temp["unknown"]:
        send_text(
            event=event,
            message=templates.high_temp_unknown,
            require_read=False,
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
    elif status == status_code.high_temp["end"]:
        # Send clinic info and ask to go see doctor ASAP
        clinic = templates.get_nearby_clinic(message)

        if isinstance(clinic, LocationSendMessage):
            send_location(
                event=event,
                location=clinic,
                socketio=socketio,
                user_id=user_id
            )

            send_text(
                event=None,
                message=templates.high_temp_asap,
                require_read=False,
                socketio=socketio,
                user_id=user_id
            )

        else:
            send_text(
                event=event,
                message=clinic,
                require_read=False,
                socketio=socketio,
                user_id=user_id
            )

        db.update_status(
            status=status_code.system["null_state"], user_id=user_id)


def wait(event=None, socketio=None, user_id=None):

    send_text(
        event=event,
        message=templates.system_wait_admin,
        require_read=True,
        socketio=socketio,
        user_id=user_id
    )
