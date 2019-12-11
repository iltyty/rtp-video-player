import cv2
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtMultimedia import *

from logic import LogicHandler

class ClientGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.resize(800, 600)
        self.setWindowIcon(QIcon('../img/icon.png'))
        self.setWindowTitle('Video Player')
        self.setObjectName('Video Player')

        self.speeds  = ['1.0', '0.5', '2.0']
        self.clarity = ['高清', '超清',  '流畅']

        self.playslider  = QSlider(Qt.Horizontal)
        self.voiceslider = QSlider(Qt.Horizontal)
        self.btnplay  = QPushButton()
        self.btnplay.setIcon(QIcon('../img/play.png'))
        self.btnforward = QPushButton()
        self.btnforward.setIcon(QIcon('../img/forward.png'))
        self.btnaudio = QPushButton()
        self.btnaudio.setIcon(QIcon('../img/audio.png'))
        self.btnfull = QPushButton()
        self.btnfull.setIcon(QIcon('../img/full.png'))
        self.btnbarrage  = QRadioButton('弹幕')
        self.lblvideo = QLabel()
        self.lblvideo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lblvideo.setScaledContents(True)
        # self.lblvideo.setPixmap(self.imgtest)
        self.btnspeed    = QComboBox()
        self.btnspeed.addItems(self.speeds)
        self.btnclarity = QComboBox()
        self.btnclarity.addItems(self.clarity)
        self.lblspeed    = QLabel('倍速')
        self.lblclarity  = QLabel('清晰度')
        self.lblprogress = QLabel('00:00:00')
        self.lblduration = QLabel('00:00:00')

        self.phlayout = QHBoxLayout()
        self.phlayout.setObjectName('Play Horizontal Layout')
        self.phlayout.addWidget(self.lblvideo)

        self.shlayout = QHBoxLayout()
        self.shlayout.setObjectName('Slider Horizontal Layout')
        self.shlayout.setSpacing(6)
        self.shlayout.addWidget(self.lblprogress)
        self.shlayout.addWidget(self.playslider)
        self.shlayout.addWidget(self.lblduration)

        self.chlayout = QHBoxLayout()
        self.chlayout.setObjectName('Control Horizontal Layout')
        self.chlayout.addWidget(self.btnplay)
        self.chlayout.addWidget(self.btnforward)
        self.chlayout.addStretch(1)
        self.chlayout.addWidget(self.btnaudio)
        self.chlayout.addWidget(self.voiceslider)
        self.chlayout.addWidget(self.lblspeed)
        self.chlayout.addWidget(self.btnspeed)
        self.chlayout.addWidget(self.btnbarrage)
        self.chlayout.addWidget(self.lblclarity)
        self.chlayout.addWidget(self.btnclarity)
        self.chlayout.addWidget(self.btnfull)

        self.vlayout = QVBoxLayout()
        self.vlayout.setObjectName('Main Vertical Layout')
        self.vlayout.setSpacing(10)
        self.vlayout.addLayout(self.phlayout)
        self.vlayout.addLayout(self.shlayout)
        self.vlayout.addLayout(self.chlayout)

        self.setLayout(self.vlayout)

        self.show()

    def get_hms(self, time_):
        """
        Transform seconds to hour:minute:second format
        """
        hours = time_ // 3600
        mins = (time_ % 3600) // 60
        secs = time_ % 60
        return (hours, mins, secs)

    @pyqtSlot(str)
    def show_info_dialog(self, msg):
        QMessageBox.information(self, 'information', msg)

    @pyqtSlot(str)
    def update_frame(self, filename):
        """Update the movie frame according to temp image file"""
        self.lblvideo.setPixmap(QPixmap(filename))

    @pyqtSlot(int)
    def update_progress(self, play_time):
        (hours, mins, secs) = self.get_hms(play_time)
        self.lblprogress.setText('{:0>2d}:{:0>2d}:{:0>2d}'.format(hours, mins, secs))
        self.playslider.setValue(self.playslider.value() + 1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = ClientGUI()
    sys.exit(app.exec_())
