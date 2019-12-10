
class Request:
    def __init__(self, req_msg):
        if not req_msg:
            return None

        self.lines = req_msg.split('\n')
        self.seqnum = self.lines[1].split()[1]
