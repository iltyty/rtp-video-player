import cv2

class VideoFrame:
    def __init__(self, filename):
        self.filename = filename
        try:
            self.vidcap = cv2.VideoCapture(filename)
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
