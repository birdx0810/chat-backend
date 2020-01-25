# -*- coding: UTF-8 -*-
'''
The script for event handling (a.k.a the dirty part)
- Scene R: Registration
- Scene QA: Customer Service
- Scene 1: High Temperature Detected
- Scene 2: Push Disease News
'''
# Import required modules
import re

import database as db
import qa_utils

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
        sess.status[userid]['sess_status'] = 'r0'
        return 'r0'
    # Get user Chinese name
    elif not result and sess.status[userid]['sess_status'] == 'r0':
        print('Scenario 0: r1')
        if re.match(r'[\u4e00-\u9fff]{2,4}', message):
            sess.status[userid]["user_name"] = message
            sess.status[userid]['sess_status'] = 'r1'
            return 'r1'
        else:
            return "r_err"
    # Get user birthdate
    elif not result and sess.status[userid]['sess_status'] == 'r1':
        # Try parsing string to integer
        try: 
            year = int(message[0:4])
            month = int(message[4:6])
            day = int(message[6:8])
        except:
            return "r_err"
        birth = str(year) + '-' + str(month) + '-' + str(day)
        # Check if string is legal birth date
        if len(message) == 8 and year <= current_year and 1 <= month <= 12 and 1 <= day <= 31:
            sess.status[userid]["user_bday"] = birth
            sess.status[userid]['sess_status'] = 'r2'
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
    # TODO
    if stat == 'qa0':
        found = False
        # Keyword Matching
        for keys, values in qa_utils.qa_dict.items():
            for keyword in keys:
                if keyword in msg:
                    found = True
                    msg = f"你想問的問題可能是:{repr(values[0])}\n我們的回答是:{repr(values[1])}\n請問是否是你想要問的問題嗎？"
                    return "qa_2"
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
            return "qa_2"
    pass

##############################
# Scenario 1: Detected high temperature from user smart-band
##############################
def high_temp(userid, stat, sess):
    # TODO
    pass

##############################
# Scenario 2: Push news to user from CDC.gov.tw
##############################
def push_news():
    # TODO
    pass
