# -*- coding: UTF-8 -*-
# Import required modules
from datetime import datetime
import pickle
import os
import signal
import sys
import database as db
import json

class Log():
    def __init__(self):
        # Log file path
        self.path = './logs/app.log'

    def signal_handler(self, signal):
        '''
        Gracefully shutdown and close handlers
        '''
        logging.shutdown()

class Session():
    def __init__(self):
        # Session file path
        self.dirpath = os.path.abspath(
            f"{os.path.abspath(__file__)}/../session/"
        )
        self.path = f"{self.dirpath}/session.pickle"
        # User session status
        self.status = {}
        # Initial state
        self.init_state = None
        # Highlighter for debug
        self.highlight = '******************************\n'

    def signal_handler(self, signal, frame):
        '''
        Saves the session state when process is killed
        '''
        print(f'\nPressed Ctrl+C')
        # db.sync(self)
        self.save_session()
        sys.exit(0)

    def save_session(self):
        '''
        Save session to a pickle file
        '''
        if not os.path.exists(self.dirpath):
            os.makedirs(self.dirpath)

        with open(self.path, 'wb') as f:
            pickle.dump(self.status, f)
        print(f"\n{self.highlight}Saved session to \"{self.path}\"\n{self.highlight}")

    def load_session(self):
        '''
        Load session from pickle file
        '''
        if os.path.exists(self.path):
            with open(self.path, 'rb') as f:
                self.status = pickle.load(f)
            print(f"\n{self.highlight}Retrieved session file with {len(self.status)} users\n{self.highlight}")
        else:
            print(f"\n{self.highlight}No session file found. Using a new session.\n{self.highlight}")

    def add_status(self, user_id):
        '''
        Add new user to dict.
        '''
        self.status[user_id] = {}
        self.status[user_id]["user_name"] = None
        self.status[user_id]["user_bday"] = None
        self.status[user_id]["last_msg"] = None
        self.status[user_id]["sess_status"] = 'r'
        self.status[user_id]["sess_time"] = datetime.now().timestamp() # .strftime("%Y-%m-%d %H:%M:%S")
        print(f'New user: {user_id}')

    def get_status(self, user_id):
        '''
        Checks the status of the user
        If user not found, add user to dict and return `status = 'r0'` to trigger registration
        Returns a status. Do not use to trigger any other function!!!
        '''
        try:
            stat = self.status[user_id]["sess_status"]
            return stat
        except:
            self.add_status(user_id)
            stat = self.status[user_id]["sess_status"]
            return stat

    def get_user_name(self, user_id):
        '''
        Get user name 
        '''
        return self.status[user_id]["user_name"]


    def switch_status(self, user_id, status):
        '''
        Switch user status and log time
        '''
        self.status[user_id]["sess_status"] = status
        self.status[user_id]["sess_time"] = datetime.now().timestamp()# .strftime("%Y-%m-%d %H:%M:%S")
        print(f'User {user_id} status update `{status}` @ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    def get_users(self):
        '''
        Returns all users in session as a list
        '''
        users = []
        for user in self.status:
            users.append(user)
        return users

# Unit test for log or session
if __name__ == "__main__":
    pass