
class Request:
    def __init__(self, req_msg):
        if not req_msg:
            return None

        self.lines = req_msg.split('\n')
        self.seqnum = self.lines[1].split()[1]
        self.reqtype = self.lines[0].split()[0]
        self.filename = self.lines[0].split()[1]
        self.header = {}

        for line in self.lines[1:]:
            if not len(line.strip()):
                return

            line = line.strip()
            key = line.split(': ')[0]
            value = line.split(': ')[1]
            self.header[key] = value

    def __str__(self):
        return '\n'.join(self.lines)
