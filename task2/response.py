
class Response:
    def __init__(self, status_code, header={}):
        self.status_code = status_code
        self.header = header

        self.resp = {
            200: 'OK',
            455: 'Method Not Valid in This State',
            501: 'Method Not Implemented'
        }


    def __str__(self):
        line = 'RTSP/2.0 {} {}\n'.format(self.status_code, self.resp[self.status_code])
        header = ''.join(['{}: {}\n'.format(k, v) for k, v in self.header.items()])
        return line + header

    @classmethod
    def from_str(cls, msg):
        lines = msg.strip().split('\n')
        code = lines[0].split()[1]
        phrase = lines[0].split()[2]

        header = {}

        for line in lines[1:]:
            if not len(line.strip()):
                return

            key = line.split(': ')[0]
            value = line.split(': ')[1]
            header[key] = value

        return cls(code, header)
