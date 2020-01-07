# -*- coding: UTF-8 -*-
# Import required modules
import pickle
import time
import signal

class Session():
    def __init__(self):
        # Session file path
        self.path = './session/session.pickle'
        # User session status
        self.status = {}
        # Initial state
        self.init_state = None

    def signal_handler(self, signal):
        '''
        Saves the session state when process is killed
        '''
        self.save_session()
        sys.exit(0)

    def save_session(self):
        '''
        Save session to a pickle file
        '''
        pickle.dump(self.status, )

    def add_status(self, userid):
        '''
        Add new user to dict.
        '''
        self.status[userid] = {}
        self.status[userid]["user_name"] = None
        self.status[userid]["user_bday"] = None
        self.status[userid]["last_msg"] = None
        self.status[userid]["sess_status"] = 'r0'
        self.status[userid]["sess_time"] = time.time()
        print(f'New user: {userid}')

    def get_status(self, userid):
    '''
    Checks the status of the user. If user not found, add user to dict and trigger registration.
    '''
    try:
        stat = status[userid]["sess_status"]
        return stat
    except:
        self.add_status(userid)
        stat = status[userid]["sess_status"]
        return stat

    def switch_status(self, userid, status):
        '''
        Switch user status and log time
        '''
        self.status[userid]["sess_status"] = self.status
        self.status[userid]["sess_time"] = time.time()

    def update_msg(self, userid, msg):
        '''
        Update the last message sent to user
        '''
        self.status[userid]["last_msg"] = msg

    def get_msg(self, userid):
        '''
        Gets the last message sent to user
        '''
        return self.status[userid]["last_msg"]

    
            