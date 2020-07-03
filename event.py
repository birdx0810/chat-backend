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
import status_code

keys = environment.get_key()
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
    if status == status_code.registration["init_new_user"]:
        return db.update_status(status=status_code.registration["ask_user_name"], user_id=user_id)

    # Get user Chinese name
    if status == status_code.registration["ask_user_name"]:
        if 0 < len(message) <= 20 and re.match(r"[\u4e00-\u9fff]{1,20}", message):
            db.update_user_name(user_id=user_id, user_name=message)
            return status_code.registration["ask_birth_day"]
        return status_code.registration["error"]

    # Get user birthday
    if status == status_code.registration["ask_birth_day"]:
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
            return status_code.registration["error"]
        db.update_user_bday(user_id=user_id, user_bday=user_bday)
        return status_code.registration["end"]
    raise ValueError(f"Invalid status code: {status}")

##############################
# QA Flow
# qa0: User asks(sends) a question
# qa1: User replies if answer matched question
##############################


def qa(event=None, message=None, status=None):
    """
    Event handler for QA
    """

    user_id = event.source.user_id

    if status == status_code.qa["initialization"]:
        return db.update_status(status=status_code.qa["received_question"], user_id=user_id)

    if status == status_code.qa["found_question"]:
        if message in templates.T:
            return db.update_status(status=status_code.qa["is_correct_question"], user_id=user_id)
        if message in templates.F:
            return db.update_status(status=status_code.qa["not_correct_question"], user_id=user_id)
        return status_code.qa["found_unknown"]

    if status == status_code.qa["fail_to_find_question"]:
        if message in templates.T:
            return db.update_status(status=status_code.qa["contact_customer_service"], user_id=user_id)
        if message in templates.F:
            return db.update_status(status=status_code.qa["is_correct_question"], user_id=user_id)
        return status_code.qa["not_found_unknown"]

    if status == status_code.qa["not_correct_question"]:
        if message in templates.F or \
           message in [qa_obj["question"] for qa_obj in templates.qa_list]:
            return db.update_status(status=status_code.qa["user_label_answer"], user_id=user_id)
        return status_code.qa["label_unknown"]

    raise ValueError(f"Invalid status code: {status}")

##############################
# Scenario 1: Detected high temperature from user smart-band
##############################


def high_temp(event=None, message=None, status=None):
    """
    High temperature event handler and push message
    """
    if event is None:
        raise ValueError("Event must not be None")

    user_id = event.source.user_id

    if status == status_code.high_temp["initialization"]:
        # API triggered, will ask if not feeling well (T/F reply)
        if message in templates.T:
            return db.update_status(status=status_code.high_temp["user_not_feeling_well"], user_id=user_id)
        if message in templates.F:
            return db.update_status(status=status_code.high_temp["user_not_feeling_well"], user_id=user_id)
        return status_code.high_temp["user_feeling_unknown"]

    if status == status_code.high_temp["user_not_feeling_well"]:
        # Check for symptoms in reply (doctor)
        for symptom in templates.symptoms_list:
            if message == symptom["label"]:
                return db.update_status(status=symptom["status"], user_id=user_id)

        return db.update_status(status=status_code.high_temp["other_symptom"], user_id=user_id)

    if status in [
        status_code.high_temp["皮膚出疹"],
        status_code.high_temp["眼窩痛"],
        status_code.high_temp["喉嚨痛"],
        status_code.high_temp["咳嗽"],
        status_code.high_temp["咳血痰"],
        status_code.high_temp["肌肉酸痛"]
    ]:
        if message in templates.T:
            return db.update_status(status=status_code.high_temp["need_clinic_info"], user_id=user_id)
        if message in templates.F:
            return db.update_status(status=status_code.high_temp["dont_need_clinic_info"], user_id=user_id)
        return status_code.high_temp["unknown"]

    if status == status_code.high_temp["need_clinic_info"]:
        return db.update_status(status=status_code.high_temp["end"], user_id=user_id)

    raise ValueError(f"Invalid status: {status}")
