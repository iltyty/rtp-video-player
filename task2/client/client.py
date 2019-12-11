import sys

from PyQt5.QtWidgets import *

from gui import ClientGUI
from logic import LogicHandler
from gui_logic import GuiLogic

class Client:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.gui = ClientGUI()
        self.logic = LogicHandler('1.mp4')
        self.guilogic = GuiLogic(self.gui)

        self.bind_signals_slots()

        self.logic.connect_to_server()
        self.logic.send_describe()

        sys.exit(self.app.exec_())

    # Connect all signals to their correspondign slots
    def bind_signals_slots(self):
        self.logic.connect_failed_signal.connect(self.gui.show_info_dialog)
        self.logic.desc_resp_received_signal.connect(self.guilogic.set_video_info)

        self.gui.btnplay.clicked.connect(self.logic.play_btn_clicked)
        self.gui.btnplay.clicked.connect(self.guilogic.play_btn_clicked)
        self.gui.btnforward.clicked.connect(self.logic.fast_forward)
        self.gui.btnfull.clicked.connect(self.guilogic.full_screen)
        self.gui.btnaudio.clicked.connect(self.guilogic.btn_audio_clicked)
        self.gui.btnspeed.currentTextChanged.connect(self.guilogic.speed_changed)
        self.gui.btnclarity.currentTextChanged.connect(self.logic.set_clarity)
        self.gui.playslider.sliderMoved.connect(self.logic.play_slider_moved)
        self.gui.playslider.sliderMoved.connect(self.guilogic.play_slider_moved)
        self.gui.playslider.sliderReleased.connect(self.logic.play_slider_moved)
        self.gui.playslider.sliderReleased.connect(self.guilogic.play_slider_moved)

        self.guilogic.frame_update_signal.connect(self.gui.update_frame)
        self.guilogic.progress_update_signal.connect(self.gui.update_progress)

if __name__ == '__main__':
    Client()
