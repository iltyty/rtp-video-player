import sys
import time
import random
import socket
import string
import threading

from RtpPacket import RtpPacket
from VideoFrame import VideoFrame

# transmission status
INIT = 0
READY = 1
PLAYING = 2


class ClientInfo:
    """
    Instantiated when server accept a new client.
    Store all the necessary client information.
    addr, lines, seqnum, signal, rtspsock, rtpport, rtpsock, videoframe
    """

    def __init__(self, addr, rtspsock):
        self.addr = addr
        self.sessionid = random.randint(100000, 999999)
        self.rtpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtspsock = rtspsock
        self.teardown = False
        self.status = INIT
        self.signal = threading.Event()


class Server:
    BUF_SIZE  = 2048
    RTSP_PORT = 5544

    def __init__(self):
        if len(sys.argv) > 1:
            self.rtspPort = sys.argv[1]
        else:
            self.rtspPort = self.RTSP_PORT

        self.call = {
            'SETUP': self.process_setup,
            'PLAY': self.process_play,
            'PAUSE': self.process_pause,
            'TEARDOWN': self.process_teardown
        }
        self.resps = {
            200: 'OK',

            404: 'File Not Found',
            405: 'Method Not Allowed',
        }

        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtspSocket.bind(('0.0.0.0', self.rtspPort))
        self.rtspSocket.listen(10)

    def print_log(self, msg):
        curTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print('\033[31m{} \033[0m: \033[32m{}\033[0m'.format(curTime, msg))

    def serve(self):
        self.print_log('RTSP server starts running on port {}'.format(self.rtspPort))
        while True:
            cliSock, cliAddr = self.rtspSocket.accept()
            threading.Thread(target=self.serve_solo, args=(cliSock, cliAddr)).start()

    def serve_solo(self, cliSock, cliAddr):
        clientInfo = ClientInfo(cliAddr, cliSock)
        while not clientInfo.teardown:
            clientInfo.msg = clientInfo.rtspsock.recv(self.BUF_SIZE).decode()
            if clientInfo.msg:
                clientInfo.lines = clientInfo.msg.split('\n')
                clientInfo.seqnum = clientInfo.lines[1].split()[1]
                self.print_log('Data received: \n{}'.format(clientInfo.msg))
                self.process_msg(clientInfo)

    def process_msg(self, clientInfo):
        req_type = clientInfo.lines[0].split()[0]

        try:
            self.call[req_type](clientInfo)
        except KeyError:
            # illgal method
            self.process_unknown(clientInfo)

    def process_setup(self, clientInfo):
        if clientInfo.status == INIT:
            self.print_log('Process method SETUP')
            dirname = clientInfo.lines[0].split()[1]
            try:
                clientInfo.videoframe = VideoFrame(dirname)
                clientInfo.status = READY
            except FileNotFoundError:
                # sequence number in line 1, e.g, CSeq 1
                self.send_rtsp_resp(404, clientInfo)
                return
            else:
                self.send_rtsp_resp(200, clientInfo)
                # client rtp port in line 2
                clientInfo.rtpport = int(clientInfo.lines[2].split()[3])
        else:
            self.print_log('Abort redundant SETUP method')

    def process_play(self, clientInfo):
        if clientInfo.status == READY:
            clientInfo.status = PLAYING
            clientInfo.signal.clear()
            self.print_log('Process method PLAY')
            self.send_rtsp_resp(200, clientInfo)

            threading.Thread(target=self.send_rtp_pkt, args=(clientInfo,)).start()
        else:
            self.print_log('Abort redundant PLAY method')

    def process_pause(self, clientInfo):
        if clientInfo.status == PLAYING:
            clientInfo.status = READY
            self.print_log('Process method PAUSE')
            clientInfo.signal.set()
            self.send_rtsp_resp(200, clientInfo)
        else:
            self.print_log('Abort out-of-order PAUSE method')

    def process_teardown(self, clientInfo):
        self.print_log('Process method TEARDOWN')
        clientInfo.signal.set()
        clientInfo.rtpsock.close()
        clientInfo.teardown = True
        self.send_rtsp_resp(200, clientInfo)

    def process_unknown(self, clientInfo):
        self.print_log('Receive unknown method: {}'.format(clientInfo.msg.split('\n')[0].split()[0]))
        self.send_rtsp_resp(405, clientInfo)

    def send_rtsp_resp(self, status_code, clientInfo):
        # Generate random 64-bit session id
        # sessionId = ''.join([random.choice(string.ascii_lowercase) for _ in range(64)])
        info = {
            'code': status_code,
            'phrase': self.resps[status_code],
            'seq': clientInfo.seqnum,
            'session': clientInfo.sessionid,
        }
        resp = 'RTSP/1.0 {code} {phrase}\nCSeq: {seq}\nSession: {session}'.format(**info)
        self.print_log('Send RTSP response:\n{}'.format(resp))
        clientInfo.rtspsock.send(resp.encode())

    # Send RTP packets(picture) to client
    def send_rtp_pkt(self, clientInfo):
        while not clientInfo.signal.is_set():
            data = clientInfo.videoframe.next_pkt()
            # transmission completed
            if not data:
                return
            seqnum = clientInfo.videoframe.get_pktnum()
            rtppkt = self.pack_rtp_pkt(data, seqnum)

            clientInfo.rtpsock.sendto(rtppkt, (clientInfo.addr[0], clientInfo.rtpport))

    def pack_rtp_pkt(self, data, seqnum):
        """Packetize picture data into RTP packet"""
        rtppkt = RtpPacket()
        rtppkt.encode(2, 0, 0, 0, seqnum, 0, 26, 0, data)

        return rtppkt.getPacket()


def main():
    Server().serve()


if __name__ == '__main__':
    main()
