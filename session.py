# Import 
import time

class Session():

    def __init__(self):
        # User session status
        self.status = {}
        # Initial state
        self.init_state = None

    def get_status(self, userid):
        return status[userid]

    def add_status(self, userid):
        self.status[userid] = {}
        self.status[userid]["user_name"] = None
        self.status[userid]["user_bday"] = None
        self.status[userid]["last_msg"] = None
        self.status[userid]["sess_status"] = 'r0'
        self.status[userid]["sess_time"] = time.time()
        print(self.status[userid])

    def switch_status(self, userid, status):
        self.status[userid]["sess_status"] = self.status
        self.status[userid]["sess_time"] = time.time()

            