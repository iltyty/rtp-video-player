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

        # self.logic.connect_to_server()
        # self.logic.setup()

        sys.exit(self.app.exec_())

    # Connect all signals to their correspondign slots
    def bind_signals_slots(self):
        self.logic.frame_received_signal.connect(self.gui.update_frame)
        self.logic.connect_failed_signal.connect(self.gui.show_info_dialog)

        self.gui.btnplay.clicked.connect(self.logic.play_btn_clicked)
        self.gui.btnfull.clicked.connect(self.guilogic.full_screen)
        self.gui.btnaudio.clicked.connect(self.guilogic.btn_audio_clicked)

if __name__ == '__main__':
    Client()
