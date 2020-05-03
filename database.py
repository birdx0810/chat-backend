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
def log(conn, userid, message, sess):
    '''
    Log user messages and the replies of bot to DB
    '''
    qry = "INSERT INTO mb_logs (user_id, message, reply, timestamp) VALUES %s, %s, %s"
    time = datetime.datetime.now()
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    update(conn, qry, (userid, message, time))

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

    # Get session dict
    status = session.status

    # User absent in session
    try:
        for res in result:
            if res[0] not in status.keys():
                session.status[res[0]] = {}
                session.status[res[0]]["user_name"] = res[1]
                session.status[res[0]]["user_bday"] = res[2]
                session.status[res[0]]["last_msg"] = None
                session.status[res[0]]["sess_status"] = None
                session.status[res[0]]["sess_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session.save_session()
        # User absent in DB
        for userid in status.keys():
            if userid not in users:
                qry = """INSERT INTO mb_user (line_id, user_name, user_bday) VALUES (%s, %s, %s)"""
                var = (userid, status[userid]["user_name"], status[userid]["user_bday"])
                update(qry, var)
    except:
        print("An error has occured while syncing")

    print(f"Done syncing {len(status)} user records")

def get_users():
    '''
    Gets the `line_id` and `user_name` for all users
    '''
    conn = mariadb.connect(**config)
    qry = """SELECT line_id, user_name FROM mb_user"""
    result = query(qry)
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

# Unit test for database
if __name__ == "__main__":
    qry = "SELECT * FROM mb_user"
    try:
        conn = mariadb.connect(**config)
        c = conn.cursor()
        c.execute(qry)
        results = c.fetchall()
    finally:
        c.close()
        conn.close()
    print(results)
