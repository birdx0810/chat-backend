# -*- coding: UTF-8 -*-
# Import system modules
from datetime import timedelta, datetime
import json
import os
import traceback

# Import 3rd-Party Dependencies
import flask
from flask_cors import CORS
from flask import (
    Flask, abort, request
)
from flask_socketio import SocketIO
from werkzeug.serving import WSGIRequestHandler

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, StickerMessage,
    ImageMessage, VideoMessage, AudioMessage
)

# Import local modules
import database as db
import event as e
import responder
import templates
import environment

##############################
# Application & variable initialization
##############################

config = environment.get_server_config()

# Initialize Flask
app = Flask(__name__, static_folder=None)
cors = CORS(app, resources={
    r"/login": {"Access-Control-Allow-Credentials": True},
    r"/users": {"Access-Control-Allow-Credentials": True},
    r"/messages": {"Access-Control-Allow-Credentials": True},
    r"/send": {"Access-Control-Allow-Credentials": True}
})
app.config["SERVER_NAME"] = config["server_name"]
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

WSGIRequestHandler.protocol_version = "HTTP/1.1"

keys = environment.get_key()
# Channel Access Token
line_bot_api = LineBotApi(keys[0])
# Channel Secret
handler = WebhookHandler(keys[1])

##############################
# Callback API (LINE)
##############################
# Listen to all POST requests from HOST/callback


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    # app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return "OK"

# API for triggering event.high_temp case
# Accepts a json file with user name and birth


@app.route("/event_high_temp", methods=["POST"])
def high_temp():
    if request.headers["Content-Type"] != "application/json":
        return abort(400, "Bad Request: Please use `json` format")
    try:
        # Known issue user name and birthday conflict
        data = request.json
        user_id = db.get_user_id(birth=data["birth"], name=data["name"])
        if user_id is None:
            raise ValueError(
                f"User ID not found:\nUsername: {data['name']}\nUser BDay: {data['birth']}")
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(404, "Not Found: User ID not found")

    status = db.update_status(status="s1s0", user_id=user_id)
    responder.high_temp(
        event=None,
        message=None,
        socketio=socketio,
        status=status,
        user_id=user_id
    )
    return "OK"

#########################
# Frontend API
#########################


@app.route("/users", methods=["POST"])
def get_user():
    """
    - input: none
    - output:
        array[{
            user_id
            user_name,
            last_content,     //最後一個訊息的內容
            timestamp,        //最後一個訊息的時間
        }]
    """
    try:
        data = request.get_json(force=True)

        token = data["token"]

        if db.check_login(token=token) is None:
            raise ValueError(f"Invalid token {token}")

        if "timestamp_offset" in data:
            offset = data["timestamp_offset"]
        else:
            offset = 0
        if "max_amount" in data:
            max_amount = data["max_amount"]
        else:
            max_amount = 10

        users = db.get_users(
            max_amount=max_amount,
            offset=offset
        )

        temp = []

        for user in users:
            # convert `is_read` and `require_read` to boolean
            temp.append({
                "is_read": user["is_read"] == 1,
                "last_content": user["message"],
                "require_read": user["require_read"] == 1,
                "timestamp": user["timestamp"],
                "user_id": user["user_id"],
                "user_name": user["user_name"],
            })

        response = flask.Response(json.dumps(temp))
        return response

    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(403, "Forbidden: Authentication is bad")


@app.route("/messages", methods=["POST"])
def get_old_msgs():
    """
    - input:
        - user_id: string
        - timestamp_offset: timestamp
        - maxAmount: int
    - output:
        array[{
            user_id,
            user_name,
            direction,
            content,
            timestamp,
        }]
    """

    try:
        data = request.get_json(force=True)

        token = data["token"]

        if db.check_login(token=token) is None:
            raise ValueError(f"Invalid token {token}")

        user_id = data["user_id"]
        offset = data["timestamp_offset"]
        max_amount = data["max_amount"]

        user_name = db.get_user_name(user_id=user_id)

        messages = db.get_messages(
            max_amount=max_amount,
            offset=offset,
            user_id=user_id
        )
        temp = []

        for message in messages:
            if message["direction"] == 0:
                # Send sentiment scores as text to frontend
                message["message"] = templates.system_senti_scores(
                    message=message["message"],
                    senti_score=message["senti_score"],
                    accum_senti_score=message["accum_senti_score"],
                )
            # convert `is_read` and `require_read` to boolean
            temp.append({
                "content": message["message"],
                "direction": message["direction"],
                "is_read": message["is_read"] == 1,
                "require_read": message["require_read"],
                "timestamp": message["timestamp"] == 1,
                "user_id": user_id,
                "user_name": user_name,
            })

        response = flask.Response(json.dumps(temp))
        return response
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(403, "Forbidden: Authentication is bad")


@app.route("/send", methods=["POST"])
def send_msg():
    try:
        data = request.get_json(force=True)
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(400, "Bad Request: Error parsing to `json` format")

    try:
        token = data["token"]
        if db.check_login(token=token) is None:
            raise ValueError(f"Invalid token {token}")
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(403, "Forbidden: Authentication is bad")

    try:
        user_id = data["user_id"]
        message = data["message"]

        responder.send_text(
            event=None,
            message=message,
            require_read=False,
            socketio=socketio,
            user_id=user_id
        )
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(400, "Bad request: invalid message")

    return flask.Response("OK", status=200)


@app.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return flask.Response(status=200)

    token = None
    user_name = None
    password = None

    try:
        data = request.get_json(force=True)

        if "token" in data:
            token = data["token"]
        if "username" in data and "password" in data:
            user_name = data["username"]
            password = data["password"]
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return flask.Response(status=400)

    token = db.check_login(
        user_name=user_name,
        password=password,
        token=token
    )

    if token is None:
        return abort(401)

    response = flask.Response(token, status=200)

    response.set_cookie(
        key="token",
        value=token,
        max_age=int(timedelta(days=30).total_seconds()),
        expires=datetime.now() + timedelta(days=30),
        path="/",
        domain=config["server_name"]
    )

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"

    return response


@app.route("/message_is_read", methods=["POST"])
def message_is_read():
    try:
        data = request.get_json(force=True)

        token = data["token"]

        if db.check_login(token=token) is None:
            raise ValueError(f"Invalid token {token}")

        user_id = data["user_id"]
        timestamp = data["timestamp"]

        ok = db.message_is_read(
            timestamp=timestamp,
            user_id=user_id
        )

        if ok:
            response = flask.Response(status=200)
        else:
            response = flask.Response(status=400)
        return response
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return abort(403, "Forbidden: Authentication is bad")


#########################
# socket connection
#########################


@socketio.on("connect", namespace="/")
def handle_connection():
    try:
        token = request.args.get("token")

        if db.check_login(token=token) is None:
            raise ValueError(f"Invalid token {token}")
        print("SOCKET: Connected")
        socketio.emit("Response", {"data": "OK"}, broadcast=True)
        print("SOCKET: Emitted")
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        return False


@socketio.on_error()
def error_handler_chat(err):
    print(err)

##############################
# Message handler
##############################


def message_handler(event, message):
    # Retreive user_id
    user_id = event.source.user_id

    status = db.get_status(user_id=user_id)
    timestamp = db.get_last_timestamp(user_id=user_id)

    if status is None:
        db.add_user(user_id=user_id)
        status = db.get_status(user_id=user_id)

    # Trigger timeout, only ignore if in registration status
    if status not in ["r", "r0", "r1", "r_err"] and \
       timestamp is not None:
        expired = datetime.now().timestamp() - timestamp > timedelta(days=1).total_seconds()

        if expired:
            status = db.update_status(
                status='s',
                user_id=user_id
            )

    # Log user metadata
    print(f"\nUser: {user_id}")
    print(f"Message: {message}")
    print(f"Status: {status}\n")

    # Log user message to database
    _, senti_score, accum_senti_score = db.log(
        direction=0,
        message=message,
        user_id=user_id
    )

    # Send user message to frontend
    responder.send_frontend(
        direction=0,
        message=templates.system_senti_scores(
            message=message,
            senti_score=senti_score,
            accum_senti_score=accum_senti_score
        ),
        require_read=False,
        socketio=socketio,
        user_id=user_id
    )

    # User in registration
    if status in ["r", "r0", "r1", "r_err"]:
        status = e.registration(
            message=message,
            status=status,
            user_id=user_id
        )
        responder.registration(
            event=event,
            socketio=socketio,
            status=status
        )

    # User trigger predefine QA or want Custom service
    elif status == "s":
        if any([
                keyword in message
                for keyword in templates.qa_trigger
        ]):
            status = "qa0"
            db.update_status(
                status=status,
                user_id=user_id,
            )
            responder.qa(
                event=event,
                message=message,
                socketio=socketio,
                status=status
            )
        else:
            status = "w"
            db.update_status(
                status=status,
                user_id=user_id,
            )
            responder.wait(
                event=event,
                message=message,
                socketio=socketio,
                status=status,
                user_id=user_id
            )

    # User trigger predefine QA
    elif status == "w" and any([
            keyword in message
            for keyword in templates.qa_trigger
    ]):

        status = "qa0"
        db.update_status(
            status=status,
            user_id=user_id,
        )
        responder.qa(
            event=event,
            message=message,
            socketio=socketio,
            status=status
        )

    elif status in ["qa0", "qa1-1", "qa1-2", "qa2_f"]:
        status = e.qa(
            event=event,
            message=message,
            status=status
        )
        responder.qa(
            event=event,
            message=message,
            socketio=socketio,
            status=status
        )

    # User in scenario 1
    elif status in ["s1s0", "s1s1", "s1d0", "s1d1", "s1d2",
                    "s1d3", "s1d4", "s1d5", "s1df", "s1s2",
                    "s1s3", "s1s4"]:
        status = e.high_temp(
            event=event,
            message=message,
            status=status
        )
        responder.high_temp(
            event=event,
            message=message,
            socketio=socketio,
            status=status,
            user_id=user_id
        )

# Text message handler


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    Pass id, msg, and session into event function and return updated status
    Respond to user according to new status
    """
    # Get user message
    message_handler(
        event=event,
        message=event.message.text
    )


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    # Set user message as a hint
    message_handler(
        event=event,
        message=(
            f"{templates.system_sticker_message}\n" +
            f"[[package_id={event.message.package_id}]]\n" +
            f"[[sticker_id={event.message.sticker_id}]]"
        )
    )


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    # retrieve user metadata
    message_handler(
        event=event,
        message=templates.system_image_message
    )


@handler.add(MessageEvent, message=VideoMessage)
def handle_video(event):
    # retrieve user metadata
    message_handler(
        event=event,
        message=templates.system_video_message
    )


@handler.add(MessageEvent, message=AudioMessage)
def handle_audio(event):
    # retrieve user metadata
    message_handler(
        event=event,
        message=templates.system_audio_message
    )


@app.after_request
def allow_cors(response):
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Set-Cookie, *"
    response.headers["Access-Control-Allow-Origin"] = config["client_name"]
    return response

##############################
# Main function
##############################


if __name__ == "__main__":
    # Setup host port
    port = int(os.environ.get("PORT", 8080))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
