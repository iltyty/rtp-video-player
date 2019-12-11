import os
import time
import threading

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtMultimedia import *

from gui import ClientGUI

CACHE_FILE_EXT = '.jpg'

class GuiLogic(QObject):
    frame_update_signal = pyqtSignal(str)
    progress_update_signal = pyqtSignal(int)

    def __init__(self, gui):
        super().__init__()

        self.gui = gui
        self.first_play = True
        self.playing = False
        # Video sound muted or not
        self.mute = False
        # Frame rate of the video
        self.fps = 30
        # Number of total frames of the video
        self.frm_cnt = 0
        # The number of seconds of video already played
        self.play_time = 0
        # 1000ms / fps
        self.tickframe = 1000 / self.fps
        # Sleep time of video rendering thread
        # Default: 33.3ms (30 FPS)
        self.tick_play_sleep = 0.033
        # Sleep time of label/slider updating thread
        # Default: 1s (Normal play speed)
        self.tick_prog_sleep = 1
        # The previous result of perf_counter
        self.ticklast = time.perf_counter()
        # Currently displayer picture's file name
        self.filename = './cache/'
        # Currently displayed picture's index
        self.fileidx = 0

    @pyqtSlot()
    def full_screen(self):
        # self.gui.videowidget.setFullScreen(True)
        pass

    @pyqtSlot()
    def btn_audio_clicked(self):
        self.mute = not self.mute
        btn_audio = self.sender()
        if self.mute:
            btn_audio.setIcon(QIcon('../img/mute.png'))
        else:
            btn_audio.setIcon(QIcon('../img/audio.png'))

    @pyqtSlot()
    def play_btn_clicked(self):
        btn = self.sender()
        if not self.playing:
            # play button clicked
            if self.first_play:
                threading.Thread(target=self.play_thread).start()
                threading.Thread(target=self.progress_thread).start()
                self.first_play = False
            btn.setIcon(QIcon('../img/pause.png'))
            self.playing = True
        else:
            # pause button clicked
            btn.setIcon(QIcon('../img/play.png'))
            self.playing = False

    def get_hms(self, time_):
        """
        Transform seconds to hour:minute:second format
        """
        hours = time_ // 3600
        mins = (time_ % 3600) // 60
        secs = time_ % 60
        return (hours, mins, secs)

    @pyqtSlot(dict)
    def set_video_info(self, data):
        self.fps = data['Frame-Rate']
        self.frm_cnt = data['Frame-Count']
        self.tickframe = 1000 / self.fps

        # Video duration
        self.duration = int(self.frm_cnt / self.fps)
        (hours, mins, secs) = self.get_hms(self.duration)

        self.gui.lblduration.setText('{:0>2d}:{:0>2d}:{:0>2d}'.format(hours, mins, secs))
        self.gui.playslider.setMinimum(0)
        self.gui.playslider.setMaximum(self.duration)
        self.gui.playslider.setValue(0)

    @pyqtSlot()
    def speed_changed(self):
        combo_box = self.sender()
        index = combo_box.currentIndex()

        if index == 0:
            # 1.0 speed
            self.tickframe = 1000 / self.fps
            self.tick_play_sleep = 0.033
            self.tick_prog_sleep = 1
        elif index == 1:
            # 0.5 speed
            self.tickframe = 2000 / self.fps
            self.tick_play_sleep = 0.066
            self.tick_prog_sleep = 2
        else:
            # 2.0 speed
            self.tickframe = 500 / self.fps
            self.tick_play_sleep = 0.017
            self.tick_prog_sleep = 0.5

    def play_thread(self):
        """
        Video playing thread.
        Updata video frame every 1000 / fps ms
        """
        self.cur_frm = 0
        while self.cur_frm <= self.frm_cnt:
            if not self.playing:
                continue

            tickcur = time.perf_counter()
            tickdiff = 1000 * (tickcur - self.ticklast)
            self.ticklast = tickcur

            if (tickdiff - self.tickframe > 2):
                self.tick_play_sleep -= 0.001
                if self.tick_play_sleep <= 0.001:
                    self.tick_play_sleep = 0.001

            if (tickdiff - self.tickframe < -2):
                self.tick_play_sleep += 0.001

            arg = self.filename + str(self.fileidx) + CACHE_FILE_EXT
            if os.path.isfile(arg):
                self.frame_update_signal.emit(arg)
            self.cur_frm += 1
            self.fileidx += 1
            time.sleep(self.tick_play_sleep)

    def progress_thread(self):
        """
        Progress thread
        Update process label and play slider every 1/0.5/2 s
        """
        while self.cur_frm <= self.frm_cnt:
            if not self.playing:
                continue

            self.play_time += 1
            self.progress_update_signal.emit(self.play_time)
            time.sleep(self.tick_prog_sleep)

    def play_slider_moved(self):
        slider = self.sender()
        portion = slider.value() / self.duration
        frm_num = int(portion * self.frm_cnt)

        self.fileidx = 0
        self.cur_frm = frm_num
        self.play_time = slider.value()
        self.progress_update_signal.emit(self.play_time)
