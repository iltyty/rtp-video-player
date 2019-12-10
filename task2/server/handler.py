import time
import socket

class Handler:
    """
    Request handler
    """
    BUF_SIZE = 2048

    # transmission status
    INIT = 0
    READY = 1
    PLAYING = 2

    def __init__(self):
        self.state = self.INIT

        self.call = {
            'PLAY': play,
            'PAUSE': pause,
            'SETUP': setup,
            'DESCRIBE': describe,
            'TEARDOWN': teardown
        }

    def print_log(self, msg):
        curTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print('\033[31m{} \033[0m: \033[32m{}\033[0m'.format(curTime, msg))
