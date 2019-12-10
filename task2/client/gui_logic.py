from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtMultimedia import *

from gui import ClientGUI

class GuiLogic(QObject):
    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        self.mute = False

    @pyqtSlot()
    def full_screen(self):
        print('clicked')
        self.gui.videowidget.setFullScreen(True)

    @pyqtSlot()
    def btn_audio_clicked(self):
        self.mute = not self.mute
        btn_audio = self.sender()
        if self.mute:
            btn_audio.setIcon(QIcon('../img/mute.png'))
        else:
            btn_audio.setIcon(QIcon('../img/audio.png'))
