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
from datetime import datetime
import re
import json
import os

import utilities
import environment

# Is development or production
config = environment.get_config(environment.environment.get_env())

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
        print(traceback.format_exc())
    return conn

# Function factory


def query_one(qry, var):
    '''
    Function for executing `SELECT * FROM table WHERE var0=foo, var1=bar`
    '''
    rows = None

    try:
        conn = mariadb.connect(**config)
        try:
            c = conn.cursor(dictionary=True)
            c.execute(qry, var)
            rows = c.fetchone()
        except Exception as e:
            print(e)
            print(traceback.format_exc())
        finally:
            c.close()
    except Exception as e:
        print(e)
        print(traceback.format_exc())
    finally:
        conn.close()

    if rows == None:
        print("Query result is empty")

    return rows


def query_all(qry, var):
    '''
    Function for executing `SELECT * FROM table WHERE var0=foo, var1=bar`
    '''
    rows = []

    try:
        conn = mariadb.connect(**config)
        try:
            c = conn.cursor(dictionary=True)
            c.execute(qry, var)
            rows = c.fetchall()
        except Exception as e:
            print(e)
            print(traceback.format_exc())
        finally:
            c.close()
    except Exception as e:
        print(e)
        print(traceback.format_exc())
    finally:
        conn.close()

    if rows == []:
        print("Query result is empty")

    return rows


def update(qry, var):
    '''
    Function for updating DB
    '''
    is_success = False
    try:
        conn = mariadb.connect(**config)
        conn.autocommit = False
        conn.start_transaction()
        try:
            c = conn.cursor()
            c.execute(qry, var)
            is_success = True
        except mariadb.Error as e:
            print(e)
            print(traceback.format_exc())
        finally:
            c.close()

    except mariadb.Error as e:
        conn.rollback()
        print(e)
        print(traceback.format_exc())
    else:
        conn.commit()
        print("Update successful")
    finally:
        conn.close()

    return is_success

# Other functions


def log(direction=None, message=None, timestamp=None, user_id=None):
    '''
    Log user messages and the replies of bot to DB
    '''
    qry = """
        INSERT INTO mb_logs (user_id, message, direction, timestamp) 
        VALUES (%s, %s, %s, %s);
    """
    if timestamp == None:
        timestamp = datetime.now().timestamp()
    is_success = update(qry, (user_id, message, direction, timestamp))

    # TODO: Error Notification

    if direction == 0:
        direction = "FROM"
    elif direction == 1:
        direction = "TO"
    print(f"Message {direction} user {user_id} saved to DB")


def get_users():
    '''
    Gets the `user_id` and `user_name` for all users
    '''
    qry = """
        SELECT user_id, user_name
        FROM mb_user;
    """
    result = query_all(qry, None)

    return result


def get_messages(user_id=None):
    '''
    Gets all messages from database
    '''
    qry = """
        SELECT * 
        FROM mb_logs 
        WHERE user_id=%s 
        ORDER BY timestamp DESC;
    """

    result = query_all(qry, (user_id,))
    return result


def get_last_message(user_id=None):
    '''
    Get last message
    '''
    qry = """
        SELECT user_id, message
        FROM mb_logs
        WHERE user_id=%s
        ORDER BY timestamp DESC
        LIMIT 1;
    """
    result = query_one(qry, (user_id,))

    if result == None:
        return None

    return result["message"]


def get_user_id(birth=None, name=None, nric=None):
    '''
    Get user user_id with `user_name` and `user_bday`
    Returns matched user_id
    '''
    qry = """
        SELECT user_id
        FROM mb_user 
        WHERE user_name=%s AND user_bday=%s
        ORDER BY user_id ASC;
    """
    result = query_one(qry, (name, birth))

    if result == None:
        return None

    # Known issue (more than one user)
    return result["user_id"]


def get_user_name(user_id=None):
    '''
    Get user `user_name` with `user_id`
    Returns matched `user_name`
    '''
    qry = """
        SELECT user_name
        FROM mb_user
        WHERE user_id=%s;
    """
    result = query_one(qry, (user_id, ))

    if result == None:
        return None

    return result["user_name"]


def get_status(user_id=None):
    qry = """
    SELECT user_status
    FROM mb_user
    WHERE user_id=%s;
    """

    result = query_one(qry, (user_id,))

    if result == None:
        return None

    return result["user_status"]


def add_user(user_id=None):
    qry = """
        INSERT INTO mb_user (user_id)
        VALUES (%s);
    """

    is_success = update(qry, (user_id,))

    # TODO: Error Notification


def update_status(status=None, user_id=None):
    qry = """
        UPDATE mb_user
        SET user_status=%s
        WHERE user_id=%s;
    """

    is_success = update(qry, (status, user_id))

    # TODO: Error Notification

    return get_status(user_id=user_id)


def update_user_name(user_id=None, user_name=None):
    qry = """
        UPDATE mb_user
        SET user_name=%s, user_status='r1'
        WHERE user_id=%s;
    """

    is_success = update(qry, (user_name, user_id))

    # TODO: Error Notification


def update_user_bday(user_id=None, user_bday=None):
    qry = """
        UPDATE mb_user
        SET user_bday=%s, user_status='r2'
        WHERE user_id=%s;
    """

    is_success = update(qry, (user_bday, user_id))

    # TODO: Error Notification


def get_admin():
    qry = """
        SELECT admin_name, admin_pass
        FROM mb_admin;
    """
    result = query_one(qry, None)

    if result == None:
        return None

    return result


# Unit test for database
if __name__ == "__main__":
    results = get_users()
    print(results)
    # results = get_messages("U96df1b7908bfe4d71970d05f344c7694")
    # print(results)

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
