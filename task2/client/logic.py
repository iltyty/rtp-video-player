import os
import cv2
import sys
import time
import shutil
import socket
import threading

from os import path

sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from task2.response import Response
from task2.rtppkt.rtppkt import RtpPacket

CACHE_FILE_EXT  = '.jpg'
CACHE_DIRECTORY = './cache/'

class LogicHandler(QObject):
    INIT = 0
    READY  = 1
    PLAYING = 2

    status = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    DESCRIBE = 3
    TEARDOWN = 4

    BUFSIZE = 40960

    connect_failed_signal = pyqtSignal(str)
    desc_resp_received_signal = pyqtSignal(dict)

    def __init__(self, url, serveraddr='localhost', serverport=5544, rtpport=4321):
        super().__init__()

        # Cached picture's index
        self.index = 0
        self.serveraddr = serveraddr
        self.serverport = serverport
        self.rtpport = rtpport
        # Cached picture's name
        self.url = url

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
            threading.Thread(target=self.recv_rtsp_resp).start()
        except:
            self.connect_failed_signal.emit('Connection to "{}" failed!'.format(self.serveraddr))

    @pyqtSlot()
    def play_btn_clicked(self):
        if self.status == self.READY:
            self.send_play()
        elif self.status == self.PLAYING:
            self.send_pause()

    def write_frame(self, data):
        """
        Write the received frame to a temp image file. Return the file name.
        """
        cachename = CACHE_DIRECTORY + str(self.index) + CACHE_FILE_EXT
        self.index += 1
        with open(cachename, 'wb') as f:
            f.write(data)
            f.close()

        return cachename

    def send_describe(self):
        if self.status != self.INIT:
            return

        self.rtspseq += 1
        req = 'DESCRIBE ' + self.url + ' RTSP/2.0\nCSeq: ' + str(self.rtspseq)
        self.rtspsock.sendall(req.encode())
        self.reqsent = self.DESCRIBE
        time.sleep(1)
        self.send_setup()

    def send_setup(self):
        if self.status != self.INIT:
            return

        self.rtspseq += 1
        req = 'SETUP ' + self.url + ' RTSP/2.0\nCSeq: ' + str(self.rtspseq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpport)
        self.rtspsock.send(req.encode())
        self.reqsent = self.SETUP
        self.status = self.READY

    @pyqtSlot()
    def send_play(self, location=0):
        self.rtspseq += 1
        self.playevt.clear()
        threading.Thread(target=self.listen_rtp).start()

        req = 'PLAY ' + self.url + ' RTSP/2.0\nCSeq: ' + str(self.rtspseq) + \
            '\nSession: ' + str(self.sessionid) + '\nLocation: ' + str(location)
        self.rtspsock.send(req.encode())
        self.reqsent = self.PLAY
        self.status = self.PLAYING

    @pyqtSlot()
    def send_pause(self):
        if self.status != self.PLAYING:
            return

        self.rtspseq += 1
        req = 'PAUSE ' + self.url + ' RTSP/2.0\nCSeq: ' + str(self.rtspseq) + '\nSession: ' + str(self.sessionid)
        self.rtspsock.send(req.encode())
        self.reqsent = self.PAUSE
        self.status = self.READY

    @pyqtSlot()
    def send_teardown(self):
        if self.status == self.INIT:
            return

        self.rtspseq += 1
        req = 'TEARDOWN ' + self.url + ' RTSP/2.0\nCSeq: ' + str(self.rtspseq) + '\nSession: ' + str(self.sessionid)
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

    def parse_rtsp_resp(self, msg):
        """Parse the RTSP response from the server"""
        resp = Response.from_str(msg)

        # Process only if the response's sequence number is the same as the request's
        if int(resp.header['CSeq']) != self.rtspseq:
            return

        # New RTSP session id
        if self.sessionid == 0:
            self.sessionid = resp.header['Session']

        # Process only if the session id is the same
        if self.sessionid != resp.header['Session']:
            return

        if resp.status_code == '200':
            if self.reqsent == self.DESCRIBE:
                fps = float(resp.header['Frame-Rate'])
                frm_cnt = float(resp.header['Frame-Count'])
                data = {
                    'Frame-Rate': fps,
                    'Frame-Count': frm_cnt
                }
                self.fps = fps
                self.frm_cnt = frm_cnt
                self.duration = self.frm_cnt / self.fps
                self.desc_resp_received_signal.emit(data)
            elif self.reqsent == self.SETUP:
                # Initialize RTP port
                self.init_rtpport()
            elif self.reqsent == self.PAUSE:
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
        if not os.path.exists('./cache'):
            os.mkdir('./cache')
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

    def play_slider_moved(self):
        self.clear_cache()
        self.playevt.set()

        slider = self.sender()
        portion = slider.value() / self.duration
        frmnum = portion * self.frm_cnt
        self.send_play(int(frmnum))

    def clear_cache(self):
        """
        Clear the cache directory
        """
        shutil.rmtree('cache')
        os.mkdir('./cache')
        self.index = 0
