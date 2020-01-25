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
    except Exception as e:
        print(e)
    return conn

# Function factory
def query(conn, qry, var):
    '''
    Function for executing `SELECT * FROM table WHERE var0=foo, var1=bar`
    '''
    try:
        conn = mariadb.connect(**config)
        c = conn.cursor()
        c.execute(qry, var)
        rows = c.fetchall()
    except Exception as e:
        print(e)
    finally:
        c.close()
        conn.close()
    return rows

def update(conn, qry, var):
    '''
    Function for updating DB
    '''
    try:
        conn = mariadb.connect(**config)
        c = conn.cursor()
        c.execute(qry, var)
    except Error as e:
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
def log(userid, message, sess):
    '''
    Log user messages and the replies of bot to DB
    '''

    qry = "INSERT INTO mb_logs (user_id, message, reply, timestamp) VALUES (?, ?, ?)"
    time = datetime.datetime.now()
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    update(conn, qry, (userid, message, time))

def sync(sess):
    '''
    TODO: Sync session dictionary and DB
    '''
    pass

def check_user(name, birth, nric=None):
    '''
    Get user line_id with `user_name` and `user_bday`
    Returns matched line_id
    '''
    qry = """SELECT line_id FROM mb_user WHERE name=? and birth=?"""
    result = query(conn, qry, (name, birth))
    return result

# Unit test for database
if __name__ == "__main__":
    conn = connect()
    # conn = mariadb.connect(**config)
    pass
