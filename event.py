# -*- coding: UTF-8 -*-
'''
The script for event (status) handling and check for msg errors
- Scene R: Registration
- Scene QA: Customer Service
- Scene 1: High Temperature Detected
- Scene 2: Push Disease News
'''
# Import required modules
from opencc import OpenCC

from linebot import (
    LineBotApi, WebhookHandler
)

import mysql.connector as mariadb

from datetime import datetime
import re
import os
import sys

import database as db
import utilities
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
def registration(user_id, message, status):
    '''
    This is the main function for the registration flow
    Updates the sessionion dictionary and returns status of user
    '''

    message = message.strip()

    # New user_id detected (not in session)
    if status == 'r':
        return db.update_status(user_id, 'r0')
    # Get user Chinese name
    elif status == 'r0':
        if 0 < len(message) <= 20 and re.match(r'[\u4e00-\u9fff]{1,20}', message):
            db.update_user_name(message)
            return db.update_status(user_id, 'r1')
        else:
            return "r_err"
    # Get user birthdate
    elif status == 'r1':
        # Try parsing string to integer
        try:
            year = message[0:4]
            month = message[4:6]
            day = message[6:8]
            current = datetime.now()
            birthdate = datetime(year=int(year),month=int(month),day=int(day))
        except:
            return "r_err"

        # Check if string is legal birth date
        if len(message) == 8 and birthdate < current:
            session.status[user_id]["user_bday"] = birthdate
            session.switch_status(user_id, 'r2')
            # TODO: Add user to DB
            name = session.status[user_id]['user_name']
            try:
                conn = db.connect()
                qry = """INSERT INTO mb_user (user_id, user_name, user_bday) VALUES (%s, %s, %s)"""
                db.update(qry, (user_id, name, birthdate))
            except mariadb.Error as e:
                print('DB Error')
            return 'r2'
        else:
            return "r_err"

    # TODO: Add conditions in case of errors
    else:
        print(f"User already in database")
        db.sync(session)


    # if not result and user_id not in session.status:
    #     session.add_status(user_id)
    #     return 'r0'

##############################
# QA Flow
# qa0: User asks(sends) a question
# qa1: User replies if answer matched question
##############################
def qa(event, session):
    '''
    Event handler for QA
    '''

    T = ["有", "要", "有喔", "有阿", "好", "好喔", "好阿", "可",
         "可以", "可以阿", "Yes", "有一點", "一點", "一點點", "是"]
    F = ["沒有", "不要", "不", "沒", "No", "無", "否"
         "不用", "曾經有", "曾經", "以前有", "以前", "不是"]

    user_id = event.source.user_id
    text = event.message.text
    status = session.get_status(user_id)

    if status == 'qa0':
        session.switch_status(user_id, 'qa1')
        return 'qa1'

    elif status == 'qa1':
        if text in T:
            session.switch_status(user_id, 'qa2_t')
            return 'qa2_t'
        elif text in F:
            session.switch_status(user_id, 'qa2_f')
            return 'qa2_f'
        else:
            return 'qa1_err'

    elif status == 'qa2_f':
        session.switch_status(user_id, 'qa3')
        return 'qa3'

##############################
# Scenario 1: Detected high temperature from user smart-band
##############################
# TODO: change inputs
def high_temp(event, session):
    '''
    High temperature event handler and push message
    '''
    user_id = event.source.user_id
    message = event.message.text
    status = session.status[user_id]['sess_status']

    trad2sim = OpenCC("t2s")
    sim2trad = OpenCC("s2t")

    symptom = ['皮膚出疹','眼窩痛','喉嚨痛','咳嗽','咳血痰','肌肉酸痛']

    T = ["有", "要", "有喔", "有阿", "好", "好喔", "好阿", "可",
         "可以", "可以阿", "Yes", "有一點", "一點", "一點點", "是"]
    F = ["沒有", "不要", "不", "沒", "No", "無", "否"
         "不用", "曾經有", "曾經", "以前有", "以前", "不是"]

    # if status == 's1':
    #     # API triggered, will ask if not feeling well
    #     session.switch_status(user_id, 's1s0')
    #     return 's1s0'

    if status == 's1s0':
        # TODO: # API triggered, will ask if not feeling well (T/F reply)
        if message in T:
            status = 's1s1'
            session.switch_status(user_id, status)
            return status
        elif message in F:
            status = 's1f1'
            session.switch_status(user_id, status)
            return status

    elif status == 's1s1':
        # TODO: Check for symptoms in reply (doctor)
        if message == symptom[0]:
            status = 's1d0'
            session.switch_status(user_id, status)
            return status
        elif message == symptom[1]:
            status = 's1d1'
            session.switch_status(user_id, status)
            return status
        elif message == symptom[2]:
            status = 's1d2'
            session.switch_status(user_id, status)
            return status
        elif message == symptom[3]:
            status = 's1d3'
            session.switch_status(user_id, status)
            return status
        elif message == symptom[4]:
            status = 's1d4'
            session.switch_status(user_id, status)
            return status
        elif message == symptom[5]:
            status = 's1d5'
            session.switch_status(user_id, status)
            return status
        else:
            status = 's1df'
            session.switch_status(user_id, status)
            return status

    elif status in ['s1d0', 's1d1', 's1d2', 's1d3', 's1d4', 's1d5']:
        if message in T:
            status = 's1s2'
            session.switch_status(user_id, status)
            return status
        elif message in F:
            status = 's1f2'
            session.switch_status(user_id, status)
            return status

    elif status == 's1s2':
        status = 's1s3'
        session.switch_status(user_id, status)
        return status

##############################
# Scenario 2: Push news to user from CDC.gov.tw
##############################
'''
def push_news():
    # TODO: Prerequisites - Run crawler at specific time
    # TODO: Push news flow

    # 2. If there is news, push news and ask for location
    # if news:
    entities = ner_wrapper(msg)
    entities = "\n".join(set(entities))
    pass
'''

if __name__ == "__main__":
    key = environment.get_key("production")
    print(key)
