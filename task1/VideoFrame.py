import os
from time import sleep

class VideoFrame:
    def __init__(self, dirname):
        self.pktnum = 0
        self.index = -1
        self.files = os.listdir(dirname)
        self.dirname = dirname
        self.files = sorted(self.files, key=lambda x: int(x.split('.')[0]))

    # Get the next rtp packet
    def next_pkt(self):
        self.index += 1
        if self.index >= len(self.files):
            return ''

        sleep(0.033)
        filename = self.files[self.index]
        self.pktnum += 1
        with open(self.dirname + '/' + filename, 'rb') as f:
            return f.read()

    def get_pktnum(self):
        return self.pktnum
