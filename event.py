# -*- coding: UTF-8 -*-
"""
The script for event (status) handling and check for msg errors
- Scene R: Registration
- Scene QA: Customer Service
- Scene 1: High Temperature Detected
- Scene 2: Push Disease News
"""
# Import required modules
from datetime import datetime
import re
import os
import sys

from linebot import (
    LineBotApi, WebhookHandler
)

import database as db
import templates
import environment

# Setup path for other modules
sys.path.insert(0, os.path.dirname(
    os.path.realpath(__file__)) + "/./ChineseNER")

keys = environment.get_key(environment.environment.get_env())
# Channel Access Token
line_bot_api = LineBotApi(keys[0])
# Channel Secret
handler = WebhookHandler(keys[1])

##############################
# Scenario R: Registration flow
##############################


def registration(message=None, status=None, user_id=None):
    """
    This is the main function for the registration flow
    Updates the sessionion dictionary and returns status of user
    """

    message = message.strip()

    # New user_id detected (not in session)
    if status == "r":
        return db.update_status(status="r0", user_id=user_id)

    # Get user Chinese name
    if status == "r0":
        if 0 < len(message) <= 20 and re.match(r"[\u4e00-\u9fff]{1,20}", message):
            db.update_user_name(user_id=user_id, user_name=message)
            return "r1"
        return "r_err"
    # Get user birthday
    if status == "r1":
        # Try parsing string to integer
        try:
            if len(message) != 8:
                raise ValueError("Invalid message format")
            year = message[0:4]
            month = message[4:6]
            day = message[6:8]
            current = datetime.now()
            user_bday = datetime(
                year=int(year), month=int(month), day=int(day))
            if user_bday > current:
                raise ValueError("Impossible birthday")
        except Exception:
            return "r_err"
        db.update_user_bday(user_id=user_id, user_bday=user_bday)
        return "r2"
    raise ValueError(f"Invalid status code: {status}")

##############################
# QA Flow
# qa0: User asks(sends) a question
# qa1: User replies if answer matched question
##############################


def qa(event=None, status=None):
    """
    Event handler for QA
    """

    user_id = event.source.user_id
    message = event.message.text

    if status == "qa0":
        return db.update_status(status="qa1", user_id=user_id)

    if status == "qa1":
        if message in templates.T:
            return db.update_status(status="qa2_t", user_id=user_id)
        if message in templates.F:
            return db.update_status(status="qa2_f", user_id=user_id)
        return "qa1_err"

    if status == "qa2_f":
        return db.update_status(status="qa3", user_id=user_id)

    raise ValueError(f"Invalid status code: {status}")

##############################
# Scenario 1: Detected high temperature from user smart-band
##############################


def high_temp(event=None, status=None):
    """
    High temperature event handler and push message
    """
    if event is None:
        raise ValueError("Event must not be None")

    user_id = event.source.user_id
    message = event.message.text

    if status == "s1s0":
        # API triggered, will ask if not feeling well (T/F reply)
        if message in templates.T:
            return db.update_status(status="s1s1", user_id=user_id)
        if message in templates.F:
            return db.update_status(status="s1f1", user_id=user_id)
        return "s1s0_err"

    if status == "s1s1":
        # Check for symptoms in reply (doctor)
        for symptom in templates.symptoms_list:
            if message == symptom["label"]:
                return db.update_status(status=symptom["status"], user_id=user_id)

        return db.update_status(status="s1df", user_id=user_id)

    if status in ["s1d0", "s1d1", "s1d2", "s1d3", "s1d4", "s1d5"]:
        if message in templates.T:
            return db.update_status(status="s1s2", user_id=user_id)
        if message in templates.F:
            return db.update_status(status="s1f2", user_id=user_id)
        return "s1dx_err"

    if status == "s1s2":
        return db.update_status(status="s1s3", user_id=user_id)

    raise ValueError(f"Invalid status: {status}")
