# -*- coding: UTF-8 -*-
# Import 3rd-party modules
import click
import mysql.connector as mariadb
from mysql.connector import Error
from flask import current_app, g
from flask.cli import with_appcontext

# Import system modules
import datetime, re

# Connect to DB
def connect_db(path):
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
    Function for executing `SELECT * FROM table WHERE var=foo`
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
    time = time.strftime("%Y.%m.%d %H:%M:%S")
    update(conn, qry, (userid, message, time))
