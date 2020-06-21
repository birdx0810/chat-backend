# -*- coding: UTF-8 -*-
# Import system modules
from datetime import datetime, timedelta
import binascii
import os
import traceback

# Import 3rd-party modules
import mysql.connector as mariadb

import environment

# Is development or production
config = environment.get_database_config()

# Function factory


def query_one(qry, var):
    """
    Function for executing `SELECT * FROM table WHERE var0=foo, var1=bar`
    """
    row = None

    try:
        conn = mariadb.connect(**config)
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(qry, var)
            row = cursor.fetchone()
        except Exception as err:
            print(err)
            print(traceback.format_exc())
        finally:
            cursor.close()
    except Exception as err:
        print(err)
        print(traceback.format_exc())
    finally:
        conn.close()

    if row is None:
        print("Query result is empty")

    return row


def query_all(qry, var):
    """
    Function for executing `SELECT * FROM table WHERE var0=foo, var1=bar`
    """
    rows = []

    try:
        conn = mariadb.connect(**config)
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(qry, var)
            rows = cursor.fetchall()
        except Exception as err:
            print(err)
            print(traceback.format_exc())
        finally:
            cursor.close()
    except Exception as err:
        print(err)
        print(traceback.format_exc())
    finally:
        conn.close()

    if rows == []:
        print("Query result is empty")

    return rows


def update(qry, var):
    """
    Function for updating DB
    """
    is_success = False
    try:
        conn = mariadb.connect(**config)
        conn.autocommit = False
        conn.start_transaction()
        try:
            cursor = conn.cursor()
            cursor.execute(qry, var)
            is_success = True
        except mariadb.Error as err:
            print(err)
            print(traceback.format_exc())
        finally:
            cursor.close()

    except mariadb.Error as err:
        conn.rollback()
        print(err)
        print(traceback.format_exc())
    else:
        conn.commit()
        print("Update successful")
    finally:
        conn.close()

    return is_success

# Other functions


def log(direction=None, message=None, timestamp=None, user_id=None):
    """
    Log user messages and the replies of bot to DB
    """
    qry = """
        INSERT INTO mb_logs (user_id, message, direction, timestamp)
        VALUES (%s, %s, %s, %s);
    """
    if timestamp is None:
        timestamp = datetime.now().timestamp()
    update(qry, (user_id, message, direction, timestamp))

    # TODO: Error Notification

    if direction == 0:
        direction = "FROM"
    elif direction == 1:
        direction = "TO"
    print(f"Message {direction} user {user_id} saved to DB")
    return timestamp


def get_users():
    """
    Gets the `user_id` and `user_name` for all users
    """
    qry = """
        SELECT user_id, user_name
        FROM mb_user;
    """
    result = query_all(qry, None)

    return result


def get_messages(max_amount=None, offset=None, user_id=None):
    """
    Gets all messages from database
    """
    qry = """
        SELECT msg_id, user_id, message, direction, timestamp
        FROM mb_logs
        WHERE user_id=%s
        ORDER BY timestamp DESC
        LIMIT %s OFFSET %s;
    """

    result = query_all(qry, (user_id, max_amount, offset))

    return result


def get_last_message(user_id=None):
    """
    Get last message
    """
    qry = """
        SELECT message, timestamp
        FROM mb_logs
        WHERE user_id=%s
        ORDER BY timestamp DESC
        LIMIT 1;
    """
    result = query_one(qry, (user_id,))

    if result is None:
        return None, None

    return result["message"], result["timestamp"]


def get_user_id(birth=None, name=None):
    """
    Get user user_id with `user_name` and `user_bday`
    Returns matched user_id
    """
    qry = """
        SELECT user_id
        FROM mb_user
        WHERE user_name=%s AND user_bday=%s
        ORDER BY user_id ASC
        LIMIT 1;
    """
    result = query_one(qry, (name, birth))

    if result is None:
        return None

    # Known issue (more than one user)
    return result["user_id"]


def get_user_name(user_id=None):
    """
    Get user `user_name` with `user_id`
    Returns matched `user_name`
    """
    qry = """
        SELECT user_name
        FROM mb_user
        WHERE user_id=%s
        LIMIT 1;
    """
    result = query_one(qry, (user_id, ))

    if result is None:
        return None

    return result["user_name"]


def get_status(user_id=None):
    qry = """
        SELECT user_status
        FROM mb_user
        WHERE user_id=%s
        LIMIT 1;
    """

    result = query_one(qry, (user_id,))

    if result is None:
        return None

    return result["user_status"]


def add_user(user_id=None):
    qry = """
        INSERT INTO mb_user (user_id)
        VALUES (%s);
    """

    update(qry, (user_id,))

    # TODO: Error Notification


def update_status(status=None, user_id=None):
    qry = """
        UPDATE mb_user
        SET user_status=%s
        WHERE user_id=%s;
    """

    update(qry, (status, user_id))

    # TODO: Error Notification

    return get_status(user_id=user_id)


def update_user_name(user_id=None, user_name=None):
    qry = """
        UPDATE mb_user
        SET user_name=%s, user_status='r1'
        WHERE user_id=%s;
    """

    update(qry, (user_name, user_id))

    # TODO: Error Notification


def update_user_bday(user_id=None, user_bday=None):
    qry = """
        UPDATE mb_user
        SET user_bday=%s, user_status='r2'
        WHERE user_id=%s;
    """

    update(qry, (user_bday, user_id))

    # TODO: Error Notification


def check_login(user_name=None, password=None, token=None):
    qry_1 = """
        SELECT timestamp
        FROM mb_admin
        WHERE token=%s
        LIMIT 1;
    """
    result = query_one(qry_1, (token,))

    if result is not None:
        expired = datetime.now().timestamp() - \
            result["timestamp"] > timedelta(days=30).total_seconds()

        if expired:
            qry_2 = """
                UPDATE mb_admin
                SET token=%s
                WHERE token=%s;
            """
            update(qry_2, (binascii.hexlify(os.urandom(24)).decode(), token))

            return None

        qry_3 = """
            UPDATE mb_admin
            SET timestamp=%s
            WHERE token=%s;
        """

        update(qry_3, (datetime.now().timestamp(), token))

    if result is None:

        qry_4 = """
            SELECT admin_name, admin_pass
            FROM mb_admin
            WHERE admin_name=%s AND admin_pass=%s
            LIMIT 1;
        """
        is_valid = query_one(qry_4, (user_name, password))

        if is_valid is None:
            return None

        token = binascii.hexlify(os.urandom(24)).decode()
        timestamp = datetime.now().timestamp()

        qry_5 = """
            UPDATE mb_admin
            SET token=%s, timestamp=%s
            WHERE admin_name=%s AND admin_pass=%s;
        """

        is_success = update(qry_5, (token, timestamp, user_name, password))

        if not is_success:
            return None

    return token
