import cv2
import socket
import threading

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from rtppkt import RtpPacket

CACHE_FILE_EXT  = '.jpg'
CACHE_FILE_NAME = 'cache-'

class LogicHandler(QObject):
    INIT = 0
    READY  = 1
    PLAYING = 2
    status = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3

    BUFSIZE = 40960

    connect_failed_signal = pyqtSignal(str)
    frame_received_signal = pyqtSignal(str)

    def __init__(self, filename, serveraddr='localhost', serverport=5544, rtpport=4321):
        super().__init__()

        self.serveraddr = serveraddr
        self.serverport = serverport
        self.rtpport = rtpport
        self.filename = filename

        self.rtspseq = 0
        self.sessionid = 0
        self.framenum = 0
        self.teardownacked = False

        self.playevt = threading.Event()
        self.playevt.clear()

    def connect_to_server(self):
        self.rtspsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspsock.connect((self.serveraddr, self.serverport))
        except:
            self.connect_failed_signal.emit('Connection to "{}" failed!'.format(self.serveraddr))

    def setup(self):
        if self.status == self.INIT:
            self.send_setup()

    @pyqtSlot()
    def play_btn_clicked(self):
        btn = self.sender()
        if self.status == self.READY:
            # play button clicked
            btn.setIcon(QIcon('../img/pause.png'))
            self.play()
        elif self.status == self.PLAYING:
            # pause button clicked
            btn.setIcon(QIcon('../img/play.png'))
            self.pause()

    @pyqtSlot()
    def play(self):
        if self.status == self.READY:
            # Create a new thread to listen for RTP packets
            self.playevt.clear()
            threading.Thread(target=self.listen_rtp).start()
            self.send_play()

    @pyqtSlot()
    def pause(self):
        if self.status == self.PLAYING:
            self.send_pause()

    @pyqtSlot()
    def teardown(self):
        self.send_teardown()

    def write_frame(self, data):
        """Write the received frame to a temp image file. Return the file name."""
        cachename = CACHE_FILE_NAME + str(self.sessionid) + CACHE_FILE_EXT
        with open(cachename, 'wb') as f:
            f.write(data)
            f.close()

        return cachename

    def send_setup(self):
        """Send SETUP reqeust"""
        if self.status != self.INIT:
            return

        threading.Thread(target=self.recv_rtsp_resp).start()
        self.rtspseq += 1
        req = 'SETUP ' + self.filename + ' RTSP/1.0\nCSeq: ' + str(self.rtspseq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpport)
        self.rtspsock.send(req.encode())
        self.reqsent = self.SETUP

    def send_play(self):
        """Send PLAY request"""
        if self.status != self.READY:
            return

        self.rtspseq += 1
        req = 'PLAY ' + self.filename + ' RTSP/1.0\nCSeq: ' + str(self.rtspseq) + '\nSession: ' + str(self.sessionid)
        self.rtspsock.send(req.encode())
        self.reqsent = self.PLAY

    def send_pause(self):
        """Send PAUSE request"""
        if self.status != self.PLAYING:
            return

        self.rtspseq += 1
        req = 'PAUSE ' + self.filename + ' RTSP/1.0\nCSeq: ' + str(self.rtspseq) + '\nSession: ' + str(self.sessionid)
        self.rtspsock.send(req.encode())
        self.reqsent = self.PAUSE

    def send_teardown(self):
        """Send TEARDOWN request"""
        if self.status == self.INIT:
            return

        self.rtspseq += 1
        req = 'TEARDOWN ' + self.filename + ' RTSP/1.0\nCSeq: ' + str(self.rtspseq) + '\nSession: ' + str(self.sessionid)
        self.rtspsock.send(req.encode())
        self.reqsent = self.TEARDOWN

    def recv_rtsp_resp(self):
        while True:
            resp = self.rtspsock.recv(2048)
            print('Received response: \n{}\n'.format(resp.decode()))

            if resp:
                self.parse_rtsp_resp(resp.decode())

            if self.reqsent == self.TEARDOWN:
                self.rtspsock.shutdown(socket.SHUT_RDWR)
                self.rtspsock.close()
                break

    def parse_rtsp_resp(self, resp):
        """Parse the RTSP response from the server"""
        lines = resp.split('\n')
        seqnum = int(lines[1].split()[1])
        sessionid = lines[2].split()[1]
        statuscode = lines[0].split()[1]

        # Process only if the response's sequence number is the same as the request's
        if seqnum != self.rtspseq:
            return

        # New RTSP session id
        if self.sessionid == 0:
            self.sessionid = sessionid

        # Process only if the session id is the same
        if self.sessionid != sessionid:
            return

        if statuscode == '200':
            if self.reqsent == self.SETUP:
                # Update RTSP status
                self.status = self.READY
                # Initialize RTP port
                self.init_rtpport()
            elif self.reqsent == self.PLAY:
                self.status = self.PLAYING
            elif self.reqsent == self.PAUSE:
                self.status = self.READY
                self.playevt.set()
            elif self.reqsent == self.TEARDOWN:
                self.status = self.INIT
                self.teardownacked = True
        # TODO: handle other status code response

    def init_rtpport(self):
        """Initialize a RTP socket"""
        # Use UDP transmission method
        self.rtpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.rtpsock.settimeout(2)

        try:
            self.rtpsock.bind(('', self.rtpport))
        except:
            # TODO: handle bind error
            print('Bind error')

    def listen_rtp(self):
        """Listen for RTP packets"""
        height = 0
        width = 0
        video = None
        video_name = 'test.avi'
        while not self.playevt.is_set():
            try:
                data = self.rtpsock.recv(self.BUFSIZE)

                if data:
                    rtppkt = RtpPacket()
                    rtppkt.decode(data)

                    framenum = rtppkt.seqNum()

                    # Discard the late packet
                    if framenum > self.framenum:
                        self.framenum = framenum
                        payload = rtppkt.getPayload()
                        cachename = self.write_frame(payload)
                        frame = cv2.imread(cachename)
                        if not height:
                            height, width, layers = frame.shape
                            video = cv2.VideoWriter(video_name, 0, 1, (width, height))
                        video.write(frame)
                        # self.frame_received_signal.emit(cachename)
            except Exception as e:
                print(e)

                if self.playevt.is_set():
                    break

                if self.teardownacked:
                    self.rtpsock.shutdown(socket.SHUT_RDWR)
                    self.rtpsock.close()
                    break
        cv2.destroyAllWindows()
        if video:
            video.release()
