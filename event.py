# -*- coding: UTF-8 -*-
'''
The script for event handling (a.k.a the dirty part)
- Scene R: Registration
- Scene QA: Customer Service
- Scene 1: High Temperature Detected
- Scene 2: Push Disease News
'''
# Import required modules
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
    # Initialize Database Connection
    conn = db.connect()

    # TODO: Check user in DB_resp
    # qry = """SELECT * FROM mb_user WHERE line_id=?"""
    # result = var_query(conn, qry, (userid,))

    # New userid detected
    if not result and userid not in sess.status:
        sess.add_status(userid)
        return 'r0'
    # Get user Chinese name
    elif not result and sess.status[userid]['sess_status'] == 'r0':
        if re.match(r'[\u4e00-\u9fff]{2,4}', message):
            sess.status[userid]["user_name"] = message
            sess.status[userid]['sess_status'] = 'r1'
            return 'r1'
        else:
            return "r_err"
    # Get user birthdate
    elif not result and sess.status[userid]['sess_status'] == 'r1':
        year = int(message[0:4])
        month = int(message[4:6])
        day = int(message[6:8])
        birth = str(year) + '-' + str(month) + '-' + str(day) 
        if len(message)==8 and year <= current_year and 1<=month<=12 and 1<=day<=31:
            sess.status[userid]["user_bday"] = birth
            sess.status[userid]['sess_status'] = 'r2'
            # TODO: Add user to DB
            # qry = """INSERT INTO mb_user (line_id, name, birth, nric) VALUES (?, ?, ?, ?)"""
            # update(conn, qry, (userid, name, birth, nric))
            return 'r2'
        else:
            return "r_err"
    #TODO: Add conditions in case of errors

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
