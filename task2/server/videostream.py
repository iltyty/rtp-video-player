import cv2

class VideoStream:
    def __init__(self, filename):
        self.filename = filename
        self.quality = 70
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
            return cv2.imencode('.jpg', data, [cv2.IMWRITE_JPEG_QUALITY, self.quality])[1].tostring()

    def get_pktnum(self):
        return self.pktnum
