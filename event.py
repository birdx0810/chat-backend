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

# Setup path for other modules
sys.path.insert(0, os.path.dirname(
    os.path.realpath(__file__)) + "/./ChineseNER")

# Is development or production
is_development=True
if is_development:
    # Channel Access Token
    line_bot_api = LineBotApi('XEQclTuSIm6/pcNNB4W9a2DDX/KAbCBmZS4ltBl+g8q2IxwJyqdtgNNY9KtJJxfkuXbHmSdQPAqRWjAciP2IZgrvLoF3ZH2C2Hg+zZMgoy/xM/RbnoFa2eO9GV2F4E1qmjYxA0FbJm1uZkUms9o+4QdB04t89/1O/w1cDnyilFU=')
    # Channel Secret
    handler = WebhookHandler('fabfd7538c098fe222e8012e1df65740')

##############################
# Scenario R: Registration flow
##############################
def registration(event, session):
    '''
    This is the main function for the registration flow
    Updates the sessionion dictionary and returns status of user
    '''
    # Initialize variables
    userid = event.source.user_id
    message = event.message.text
    status = session.status[userid]['sess_status']

    qry = """SELECT * FROM mb_user WHERE line_id=%s"""
    result = db.query(qry, (userid,))

    # Error Catcher
    # if session.status[userid]['user_name'] is None:
        # db.sync(session)
        # if session.status[userid]['user_name'] is None:
        #     session.switch_status(userid, 'r0')
        # elif session.status[userid]['user_bday'] is None:
        #     session.switch_status(userid, 'r1')
        # elif session.status[userid]['sess_status'] in ["r", "r0", "r1", "r2", "r_err"]:
        #     session.switch_status(userid, None)

    # If user not in database
    if result is None:
        # New userid detected (not in session)
        if session.status[userid]['sess_status'] == 'r':
            session.switch_status(userid, 'r0')
            return 'r0'
        # Get user Chinese name
        elif session.status[userid]['sess_status'] == 'r0':
            if 2 <= len(message) <= 4 and re.match(r'[\u4e00-\u9fff]{2,4}', message):
                session.status[userid]["user_name"] = message
                session.switch_status(userid, 'r1')
                return 'r1'
            else:
                return "r_err"
        # Get user birthdate
        elif session.status[userid]['sess_status'] == 'r1':
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
                session.status[userid]["user_bday"] = birthdate
                session.switch_status(userid, 'r2')
                # TODO: Add user to DB
                name = session.status[userid]['user_name']
                try:
                    conn = db.connect()
                    qry = """INSERT INTO mb_user (line_id, user_name, user_bday) VALUES (%s, %s, %s)"""
                    db.update(qry, (userid, name, birthdate))
                except mariadb.Error as e:
                    print('DB Error')
                return 'r2'
            else:
                return "r_err"
    # TODO: Add conditions in case of errors
    else:
        print(f"User already in database")
        db.sync(session)

    
    # if not result and userid not in session.status:
    #     session.add_status(userid)
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

    userid = event.source.user_id
    text = event.message.text
    status = session.get_status(userid)

    if status == 'qa0':
        session.switch_status(userid, 'qa1')
        return 'qa1'

    elif status == 'qa1':
        if text in T:
            session.switch_status(userid, 'qa2_t')
            return 'qa2_t'
        elif text in F:
            session.switch_status(userid, 'qa2_f')
            return 'qa2_f'
        else:
            return 'qa1_err'

    elif status == 'qa2_f':
        session.switch_status(userid, 'qa3')
        return 'qa3'

##############################
# Scenario 1: Detected high temperature from user smart-band
##############################
# TODO: change inputs
def high_temp(event, session):
    '''
    High temperature event handler and push message
    '''
    userid = event.source.user_id
    message = event.message.text
    status = session.status[userid]['sess_status']

    trad2sim = OpenCC("t2s")
    sim2trad = OpenCC("s2t")

    symptom = ['皮膚出疹','眼窩痛','喉嚨痛','咳嗽','咳血痰','肌肉酸痛']

    T = ["有", "要", "有喔", "有阿", "好", "好喔", "好阿", "可",
         "可以", "可以阿", "Yes", "有一點", "一點", "一點點", "是"]
    F = ["沒有", "不要", "不", "沒", "No", "無", "否"
         "不用", "曾經有", "曾經", "以前有", "以前"]

    # if status == 's1':
    #     # API triggered, will ask if not feeling well
    #     session.switch_status(userid, 's1s0')
    #     return 's1s0'

    if status == 's1s0':
        # TODO: # API triggered, will ask if not feeling well (T/F reply)
        if message in T:
            status = 's1s1'
            session.switch_status(userid, status)
            return status
        elif message in F:
            status = 's1f1'
            session.switch_status(userid, status)
            return status

    elif status == 's1s1':
        # TODO: Check for symptoms in reply (doctor)
        if message == symptom[0]:
            status = 's1d0'
            session.switch_status(userid, status)
            return status
        elif message == symptom[1]:
            status = 's1d1'
            session.switch_status(userid, status)
            return status
        elif message == symptom[2]:
            status = 's1d2'
            session.switch_status(userid, status)
            return status
        elif message == symptom[3]:
            status = 's1d3'
            session.switch_status(userid, status)
            return status
        elif message == symptom[4]:
            status = 's1d4'
            session.switch_status(userid, status)
            return status
        elif message == symptom[5]:
            status = 's1d5'
            session.switch_status(userid, status)
            return status
        else:
            status = 's1df'
            session.switch_status(userid, status)
            return status

    elif status in ['s1d0', 's1d1', 's1d2', 's1d3', 's1d4', 's1d5']:
        if message in T:
            status = 's1s2'
            session.switch_status(userid, status)
            return status
        elif message in F:
            status = 's1f2'
            session.switch_status(userid, status)
            return status

    elif status == 's1s2':
        status = 's1s3'
        session.switch_status(userid, status)
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
