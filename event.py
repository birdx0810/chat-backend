# -*- coding: UTF-8 -*-
'''
The script for event handling (a.k.a the dirty part)
- Scene R: Registration
- Scene QA: Customer Service
- Scene 1: High Temperature Detected
- Scene 2: Push Disease News
'''
# Import required modules
import linebot.models.template
from linebot import (
    LineBotApi, WebhookHandler
)

from datetime import datetime
import re

import database as db
import qa_utils

# Setup path 


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
def registration(userid, message, sess):
    '''
    This is the main function for the registration flow
    Updates the session dictionary and returns status of user
    '''
    # Initialize Database Connection and Query
    conn = db.connect()

    qry = """SELECT * FROM mb_user WHERE line_id=%s"""
    result = db.query(conn, qry, (userid,))
    print(result)

    # New userid detected (not in session)
    if sess.status[userid]['sess_status'] == 'r':
        sess.switch_status(userid, 'r0')
        return 'r0'
    # Get user Chinese name
    elif not result and sess.status[userid]['sess_status'] == 'r0':
        print('Scenario 0: r1')
        if 2 <= len(message) <= 4 and re.match(r'[\u4e00-\u9fff]{2,4}', message):
            sess.status[userid]["user_name"] = message
            sess.switch_status(userid, 'r1')
            return 'r1'
        else:
            return "r_err"
    # Get user birthdate
    elif not result and sess.status[userid]['sess_status'] == 'r1':
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
            sess.status[userid]["user_bday"] = birthdate
            sess.switch_status(userid, 'r2')
            # TODO: Add user to DB
            qry = """INSERT INTO mb_user (line_id, name, birth) VALUES %s, %s, %s"""
            update(conn, qry, (userid, name, birth))
            return 'r2'
        else:
            return "r_err"
    #TODO: Add conditions in case of errors
    elif not result and userid not in sess.status:
        sess.add_status(userid)
        return 'r0'

##############################
# QA Flow
# qa0: User asks(sends) a question
# qa1: User replies if answer matched question
##############################
def qa(userid, stat, sess):
    if stat == 'qa0':
        found = False
        # Keyword Matching
        for keys, values in qa_utils.qa_dict.items():
            for keyword in keys:
                if keyword in msg:
                    found = True
                    msg = f"你想問的問題可能是:{repr(values[0])}\n我們的回答是:{repr(values[1])}\n請問是否是你想要問的問題嗎？"
                    sess.status[userid]['sess_status'] = "qa_1"
                    return "qa_1"
        # Calculate cosine similarity if no keywords found in sentence
        if found == False:
            query = qa_utils.bc.encode([msg])
            similarity = []
            for idx in range(len(qa_utils.question_embeddings)):
                query = query.transpose()
                sim = cosine_similarity(query, qa_utils.question_embeddings[idx].resize((768,1)))
                similarity.append(sim)
            max_idx, _ = max((i,v)for i,v in enumerate(similarity))
            msg = f"你想問的問題可能是:{repr(values[0])}\n我們的回答是:{repr(values[1])}\n請問是否是你想要問的問題嗎？"
            sess.status[userid]['sess_status'] = "qa_1"
            return "qa_1"
    # TODO: Label QA
    if stat == 'qa_1':
        pass

##############################
# Scenario 1: Detected high temperature from user smart-band
##############################
def high_temp(userid, stat, sess):
    # Initialize variables
    symptom = ['皮膚出疹','眼窩痛','喉嚨痛','咳嗽','咳血痰','肌肉酸痛','其他']

    if stat == 's1s0':
        # High temperature is detected and status is switched (not implemented)
        return 's1s0'
    elif stat == 's1d1' or stat == 's1s2':
        # TODO: Push dengue messages
        line_bot_api.push_message(userid, res.condition_diagnosis.text_message(res.condition_diagnosis.dengue_info())[1])
    elif stat == 's1s3' or stat == 's1s4' or stat == 's1s5':
        # TODO: Push flu messages
        line_bot_api.push_message(userid, res.condition_diagnosis.text_message(res.condition_diagnosis.flu_info())[1])
    elif code == 's1s6':
        # TODO: Push dengue and flu messages
        line_bot_api.push_message(userid, res.condition_diagnosis.text_message(res.condition_diagnosis.flu_info()+"\n"+res.condition_diagnosis.dengue_info())[1])
    # TODO: Ask for nearby clinic
    line_bot_api.push_message(userid, ask_nearby_clinic())
    pass

##############################
# Scenario 2: Push news to user from CDC.gov.tw
##############################
def push_news():
    # TODO
    pass
