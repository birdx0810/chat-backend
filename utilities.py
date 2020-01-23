# -*- coding: UTF-8 -*-
# Import required modules
import pickle
import time
import signal

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
        pickle.dump(self.status, self.path)

    def load_session(self):
        '''
        Load session from pickle file
        '''
        self.status = pickle.load(self.path)

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
        Checks the status of the user
        If user not found, add user to dict and return `status = 'r0'` to trigger registration
        Returns a status. Do not use to trigger any other function!!!
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

# Unit test for log or session
if __name__ == "__main__":
    pass