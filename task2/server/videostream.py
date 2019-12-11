import cv2

class VideoStream:
    def __init__(self, filename):
        self.filename = filename
        try:
            self.vidcap = cv2.VideoCapture(filename)
            self.fps = self.vidcap.get(cv2.CAP_PROP_FPS)
            self.frm_cnt = self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
        except Exception as e:
            raise e
        self.pktnum = 0

    # Get the next rtp packet
    def next_pkt(self):
        success, data = self.vidcap.read()
        if success:
            self.pktnum += 1
            return cv2.imencode('.jpg', data)[1].tostring()

    def get_pktnum(self):
        return self.pktnum
