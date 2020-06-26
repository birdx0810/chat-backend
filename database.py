# -*- coding: UTF-8 -*-
# Import system modules
from datetime import datetime, timedelta
import binascii
import os
import traceback

# Import 3rd-party modules
import mysql.connector as mariadb

import environment
import sentiment

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
    last_row_id = None
    try:
        conn = mariadb.connect(**config)
        conn.autocommit = False
        conn.start_transaction()
        try:
            cursor = conn.cursor()
            cursor.execute(qry, var)
            last_row_id = cursor.lastrowid
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

    return last_row_id

# Other functions


def log(direction=None, message=None, timestamp=None, user_id=None):
    """
    Log user messages and the replies of bot to DB
    """

    if timestamp is None:
        timestamp = datetime.now().timestamp()

    qry1 = """
        SELECT   mb_logs_analysis.accum_senti_score AS accum_senti_score
        FROM     mb_logs
        JOIN     mb_logs_analysis
        ON       mb_logs.msg_id=mb_logs_analysis.msg_id
        WHERE    user_id=%s
        AND      direction=0
        AND      timestamp >= %s
        ORDER BY timestamp DESC
        LIMIT    1;
    """

    last_accum_senti_score = 0

    # Get previous sentiment score within timeout of 1 day
    # Queried first to prevent asynchronous updates while logging messages
    result = query_one(
        qry1,
        (
            user_id,
            timestamp - timedelta(days=1).total_seconds()
        )
    )

    if result is not None:
        last_accum_senti_score = result["accum_senti_score"]

    qry2 = """
        INSERT INTO mb_logs
        (user_id, message, direction, timestamp, is_read, require_read)
        VALUES
        (%s, %s, %s, %s, 0, 0);
    """

    # Insert message to mb_logs
    msg_id = update(qry2, (user_id, message, direction, timestamp))

    print(
        f"Message {'from' if direction == 0 else 'to'} user {user_id} saved to DB")

    # If message was sent from user, perform sentiment analysis
    # of message and log to database
    if direction == 0:
        # Set score to 0 if not text message to prevent key error
        if message.startswith("[["):
            senti_score = 0
            accum_senti_score = last_accum_senti_score
        else:
            # Perform sentiment analysis
            senti_score = sentiment.liwc(message)
            accum_senti_score = senti_score + last_accum_senti_score
            accum_senti_score = min(max(accum_senti_score, -10), 10)

        qry3 = """
            INSERT INTO mb_logs_analysis (msg_id, senti_score, accum_senti_score)
            VALUES (%s, %s, %s);
        """

        # Log message to database
        update(qry3, (msg_id, senti_score, accum_senti_score))
        return timestamp, senti_score, accum_senti_score

    return timestamp, None, None


def get_users(max_amount=None, offset=None):
    """
    Gets the `user_id` and `user_name` for all users
    """
    qry1 = """
        SELECT mb_user.user_id   AS user_id,
               mb_user.user_name AS user_name,
               mb_logs.message   AS message,
               mb_logs.timestamp AS timestamp,
               mb_logs.is_read   AS is_read
        FROM   mb_user
        JOIN   mb_logs
        ON     mb_user.user_id=mb_logs.user_id
        WHERE  timestamp
        IN (
            SELECT   MAX(mb_logs.timestamp)
            FROM     mb_logs
            WHERE    mb_logs.user_id=user_id
            GROUP BY mb_logs.user_id
        )
        GROUP BY mb_user.user_id
        ORDER BY timestamp DESC
        LIMIT  %s
        OFFSET %s;
    """
    users = query_all(qry1, (max_amount, offset))

    qry2 = """
        SELECT   mb_logs.require_read AS require_read
        FROM     mb_user
        JOIN     mb_logs
        ON       mb_user.user_id=mb_logs.user_id
        WHERE    mb_logs.user_id=%s
        AND      mb_logs.require_read=1
        GROUP BY mb_logs.user_id
        LIMIT 1;
    """

    for user in users:
        result = query_one(qry2, (user["user_id"],))
        if result is not None:
            user["require_read"] = 1
        else:
            user["require_read"] = 0

    return users


def get_messages(max_amount=None, offset=None, user_id=None):
    """
    Gets all messages from database
    """
    qry = """
        SELECT    mb_logs.msg_id                     AS msg_id,
                  mb_logs.user_id                    AS user_id,
                  mb_logs.message                    AS message,
                  mb_logs.direction                  AS direction,
                  mb_logs.timestamp                  AS timestamp,
                  mb_logs.is_read                    AS is_read,
                  mb_logs.require_read               AS require_read,
                  mb_logs_analysis.senti_score       AS senti_score,
                  mb_logs_analysis.accum_senti_score AS accum_senti_score
        FROM      mb_logs
        LEFT JOIN mb_logs_analysis
        ON        mb_logs.msg_id=mb_logs_analysis.msg_id
        WHERE     mb_logs.user_id=%s
        ORDER BY  mb_logs.timestamp DESC
        LIMIT %s
        OFFSET %s;
    """

    result = query_all(qry, (user_id, max_amount, offset))

    return result


def get_last_timestamp(user_id=None):
    """
    Get last message
    """
    qry = """
        SELECT   MAX(timestamp) AS timestamp
        FROM     mb_logs
        WHERE    user_id=%s
        GROUP BY user_id;
    """
    result = query_one(qry, (user_id,))

    if result is None:
        return None

    return result["timestamp"]


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

        if is_success is None:
            return None

    return token


def message_is_read(timestamp=None, user_id=None):
    qry = """
        UPDATE mb_logs
        SET    is_read=1,
               require_read=0
        WHERE  user_id=%s
        AND    timestamp <= %s
        AND    is_read=0;
    """

    is_success = update(qry, (user_id, timestamp))

    if is_success:
        return True
    return False

def message_require_read(user_id=None):
    qry = """
        UPDATE   mb_logs
        SET      is_read=0,
                 require_read=1
        WHERE    user_id=%s
        ORDER BY timestamp DESC
        LIMIT 1;
    """

    is_success = update(qry, (user_id,))

    if is_success:
        return True
    return False
