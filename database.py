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

# Connect to DB
def connect(path):
    '''
    Initiallize the connection to DB
    Prints an error if fail to connect
    '''
    try:
        conn = mariadb.connect(user='user', password='password', database='medbot')
    except Error as e:
        print(e)
    return conn

# Function factory
def query(conn, qry, var):
    '''
    Function for executing `SELECT * FROM table WHERE var0=foo, var1=bar`
    '''
    c = conn.cursor()
    c.execute(qry, var)
    rows = c.fetchall()
    return rows

def update(conn, qry, var):
    '''
    Function for updating DB
    '''
    c = conn.cursor()
    c.execute(qry, var)
    conn.commit()

def delete(conn, qry, var):
    '''
    Function for deleting row in DB
    '''
    c = conn.cursor()
    c.execute(qry, var)

# Log messages to DB
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
    conn = connect_db(path)

    qry = """SELECT line_id FROM mb_user WHERE name=? and birth=?"""
    result = var_query(conn, qry, (name, birth))

    return result

# Unit test for database
if __name__ == "__main__":
    pass