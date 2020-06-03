# -*- coding: UTF-8 -*-
# Import 3rd-party modules
from flask import current_app, g
from flask.cli import with_appcontext

import mysql.connector as mariadb
from mysql.connector.errors import (
    DataError,
    OperationalError,
    ProgrammingError
)

import click

# Import system modules
import datetime, re

config = {
    'host': '127.0.0.1',
    'user': 'mb-admin',
    'password': '04bu2xeK',
    'database': 'medbot_db',
}

# Connect to DB
def connect():
    '''
    Initialize the connection to DB
    Prints an error if fail to connect
    '''
    try:
        conn = mariadb.connect(**config)
    except mariadb.Error as e:
        print(e)
    return conn

# Function factory
def query(qry, var):
    '''
    Function for executing `SELECT * FROM table WHERE var0=foo, var1=bar`
    '''
    try:
        conn = mariadb.connect(**config)
        c = conn.cursor()
        c.execute(qry, var)
        rows = c.fetchall()
        return rows
    except Exception as e:
        print(e)
    finally:
        c.close()
        conn.close()

def update(qry, var):
    '''
    Function for updating DB
    '''
    try:
        conn = mariadb.connect(**config)
        c = conn.cursor()
        c.execute(qry, var)
    except mariadb.Error as e:
        conn.rollback()
        print(e)
    else:
        conn.commit()
        print("Update successful")
    finally:
        c.close()
        conn.close()

def delete(conn, qry, var):
    '''
    Function for deleting row in DB
    '''
    c = conn.cursor()
    c.execute(qry, var)

# Other functions
def log(userid, message, direction):
    '''
    Log user messages and the replies of bot to DB
    '''
    qry = "INSERT INTO mb_logs (user_id, message, direction, timestamp) VALUES (%s, %s, %s, %s)"
    time = datetime.datetime.now()
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    update(qry, (userid, message, direction, time))
    if direction == 0:
        direction = "FROM"
    elif direction == 1:
        direction = "TO"
    print(f"Message {direction} user {userid} saved to DB")

def get_users():
    '''
    Gets the `line_id` and `user_name` for all users
    '''
    conn = mariadb.connect(**config)
    qry = """SELECT line_id, user_name FROM mb_user"""
    result = query(qry, None)
    return result

def get_messages(userid):
    '''
    Gets all messages from database
    '''
    conn = mariadb.connect(**config)
    qry = """SELECT * FROM mb_logs WHERE user_id=%s ORDER BY timestamp DESC"""
    result = query(qry, (userid,))
    return result

def check_user(name, birth, nric=None):
    '''
    Get user line_id with `user_name` and `user_bday`
    Returns matched line_id
    '''
    conn = mariadb.connect(**config)
    qry = """SELECT line_id FROM mb_user WHERE user_name=%s and user_bday=%s"""
    result = query(qry, (name, birth))
    return result

def sync(session):
    '''
    Sync session dictionary and DB
    '''
    # Get all user from DB
    try:
        conn = mariadb.connect(**config)
        c = conn.cursor()
        qry = "SELECT * FROM mb_user"
        c.execute(qry)
        result = c.fetchall()
    except mariadb.Error as e:
        print(e)

    users = [r[0] for r in result]
    messages = {}

    for user in users:
        tmp = get_messages(user)
        print(tmp)
        break

    # Get session dict
    status = session.status

    # User absent in session

    for res in result:
            if res[0] not in status.keys():
                session.status[res[0]] = {}
                session.status[res[0]]["user_name"] = res[1]
                session.status[res[0]]["user_bday"] = res[2]
                session.status[res[0]]["last_msg"] = None
                session.status[res[0]]["sess_status"] = None
                session.status[res[0]]["sess_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if session.status[res[0]]["user_name"] == None:
                session.status[res[0]]["user_name"] = res[1]
            if session.status[res[0]]["user_bday"] == None:
                session.status[res[0]]["user_bday"] = res[2]
            # session.status[res[0]]["last_msg"] = None
            if session.status[res[0]]["sess_status"] in ["r", "r0", "r1", "r2", "r_err"]:
                session.status[res[0]]["sess_status"] = None
            # session.status[res[0]]["sess_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session.save_session()
    # User absent in DB
    for userid in status.keys():
            if userid not in users:
                qry = """INSERT INTO mb_user (line_id, user_name, user_bday) VALUES (%s, %s, %s)"""
                var = (userid, status[userid]["user_name"], status[userid]["user_bday"])
                update(qry, var)

    print("An error has occured while syncing")

    print(f"Done syncing {len(status)} user records")

def get_admin():
    conn = mariadb.connect(**config)
    qry = """SELECT * FROM mb_admin"""
    result = query(qry, None)
    return result

# Unit test for database
if __name__ == "__main__":
    results = get_messages("U96df1b7908bfe4d71970d05f344c7694")
    print(results)

    # qry = "SELECT * FROM mb_user"
    # try:
    #     conn = mariadb.connect(**config)
    #     c = conn.cursor()
    #     c.execute(qry)
    #     results = c.fetchall()
    # finally:
    #     c.close()
    #     conn.close()
    # print(results)
