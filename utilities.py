# -*- coding: UTF-8 -*-
# Import required modules
import database

def register(userid, message, sess):
    '''
    This is the main function for the registration flow
    Updates the session dictionary and returns status of user
    '''
    # Initialize Database
    path = 'medbot.db'
    conn = connect_db(path)

    # Check user in DB
    qry = """SELECT * FROM mb_user WHERE line_id=?"""
    result = var_query(conn, qry, (userid,))

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
            # Add user to DB
            qry = """INSERT INTO mb_user (line_id, name, birth, nric) VALUES (?, ?, ?, ?)"""
            update(conn, qry, (userid, name, birth, nric))
            return 'r2'
        else:
            return "r_err"
    #TODO: Add conditions in case of errors
