# -*- coding: UTF-8 -*-
# Import required modules
from datetime import datetime
import pickle
import os
import signal
import sys

class Log():
    def __init__(self):
        # Log file path
        self.path = './logs/app.log'

    def signal_handler(self, signal):
        '''
        Gracefully shutdown and close handlers
        '''
        logging.shutdown()

    # TODO: Setup program logger
    '''
    logging.basicConfig(
        level=logging.DEBUG
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        datefmt='%Y-%m-%d %H-%M-%s'
        filename='./logs/app.log'
        filemode='a'
    )
    logger = logging.getLogger()

    # Log process id
    _pid = os.getpid()
    with open('./logs/service.pid', 'w') as f:
        f.write(str(_pid))
        f.close()

    # Log sysout
    syslog = os.fdopen('./log/app.log', 'a', 0)
    sys.stdout = syslog
    sys.stderr = syslog
    '''

class Session():
    def __init__(self):
        # Session file path
        self.path = './session/session.pickle'
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
        self.save_session()
        sys.exit(0)

    def save_session(self):
        '''
        Save session to a pickle file
        '''
        with open(self.path, 'wb') as f:
            pickle.dump(self.status, f)
        print(self.highlight + f'Saved session to \"{self.path}\"\n' + self.highlight)

    def load_session(self):
        '''
        Load session from pickle file
        '''
        if os.path.exists(self.path):
            with open(self.path, 'rb') as f:
                self.status = pickle.load(f)
            print(self.highlight + f'Retrieved session file with {len(self.status)} users\n' + self.highlight)
        else:
            print("No session file found. Using a new session.")
            self.status = {}

    def add_status(self, userid):
        '''
        Add new user to dict.
        '''
        self.status[userid] = {}
        self.status[userid]["user_name"] = None
        self.status[userid]["user_bday"] = None
        self.status[userid]["last_msg"] = None
        self.status[userid]["sess_status"] = 'r'
        self.status[userid]["sess_time"] = datetime.now()
        print(f'New user: {userid}')

    def get_status(self, userid):
        '''
        Checks the status of the user
        If user not found, add user to dict and return `status = 'r0'` to trigger registration
        Returns a status. Do not use to trigger any other function!!!
        '''
        try:
            stat = self.status[userid]["sess_status"]
            return stat
        except:
            self.add_status(userid)
            stat = self.status[userid]["sess_status"]
            return stat

    def switch_status(self, userid, stat):
        '''
        Switch user status and log time
        '''
        self.status[userid]["sess_status"] = stat
        self.status[userid]["sess_time"] = datetime.now()
        print(f'User {userid} status update `{status}` @ {datetime.now()}')

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
