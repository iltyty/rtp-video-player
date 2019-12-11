import cv2
import sys
import time
import random
import socket
import threading

from task2.request import Request
from task2.response import Response
from task2.rtppkt.rtppkt import RtpPacket
from videostream import VideoStream


class Handler:
    """
    Request handler
    """
    BUF_SIZE = 2048

    # transmission state
    INIT = 0
    READY = 1
    PLAYING = 2

    def __init__(self, addr):
        self.addr = addr
        self.state = self.INIT
        self.sessionid = self.random_session_id()
        self.rtpport = 0
        self.rtpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.teardown = False
        self.videostream = None
        self.signal = threading.Event()

        self.call = {
            'PLAY': self.play,
            'PAUSE': self.pause,
            'SETUP': self.setup,
            'DESCRIBE': self.describe,
            'TEARDOWN': self.teardown
        }

    def random_session_id(self):
        return random.randint(100000, 999999)

    def print_log(self, msg):
        curTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print('\033[31m{} \033[0m: \033[32m{}\033[0m'.format(curTime, msg))

    def process(self, request):
        req_type = request.reqtype
        try:
            return self.call[req_type](request)
        except KeyError:
            # unknown method
            print(req_type)
            return self.unknown(request)

    def play(self, request):
        self.print_log('Process method PLAY')

        if self.state != self.INIT:
            header = {
                'CSeq': request.seqnum,
                'Session': self.sessionid
            }
            self.signal.set()
            time.sleep(1)

            npt = int(request.header['NPT'])
            if npt:
                self.videostream.vidcap.set(cv2.CAP_PROP_POS_MSEC, npt)

            self.state = self.PLAYING
            self.signal.clear()
            threading.Thread(target=self.send_rtp_pkt).start()
            return Response(200, header)
        else:
            return Response(455)

    def pause(self, request):
        self.print_log('Process method PAUSE')

        if self.state == self.PLAYING:
            header = {
                'CSeq': request.seqnum,
                'Session': self.sessionid
            }

            self.state = self.READY
            self.signal.set()
            return Response(200, header)
        else:
            return Response(455)

    def setup(self, request):
        self.print_log('Process method SETUP')

        if self.state == self.INIT:
            header = {
                'CSeq': request.seqnum,
                'Session': self.sessionid
            }

            quality = int(request.header['Quality'])
            self.videostream.quality = quality
            self.state = self.READY
            self.rtpport = int(request.lines[2].split()[3])
            return Response(200, header)
        else:
            return Response(455)

    def describe(self, request):
        self.print_log('Process method DESCRIBE')

        header = {
            'CSeq': request.seqnum,
            'Session': self.sessionid
        }

        try:
            self.videostream = VideoStream(request.filename)
            header['Frame-Rate'] = self.videostream.fps
            header['Frame-Count'] = self.videostream.frm_cnt
            print(self.videostream.fps)
            return Response(200, header)
        except FileNotFoundError:
            return Response(404)

    def teardown(self, request):
        header = {
            'CSeq': request.seqnum,
            'Session': self.sessionid
        }

        self.print_log('Process method TEARDOWN')
        self.signal.set()
        self.rtpsock.close()
        self.teardown = True
        return Response(200, header)

    def unknown(self, request):
        self.print_log(str(request))
        self.print_log('Receive unknown method: {}'.format(request.reqtype))
        return Response(501)

    # Send RTP packets(picture) to client
    def send_rtp_pkt(self):
        while not self.signal.is_set():
            data = self.videostream.next_pkt()
            # transmission completed
            if not data:
                return
            seqnum = self.videostream.get_pktnum()
            rtppkt = self.pack_rtp_pkt(data, seqnum)

            self.rtpsock.sendto(rtppkt, (self.addr[0], self.rtpport))

    def pack_rtp_pkt(self, data, seqnum):
        """Packetize picture data into RTP packet"""
        rtppkt = RtpPacket()
        rtppkt.encode(2, 0, 0, 0, seqnum, 0, 26, 0, data)

        return rtppkt.getPacket()
