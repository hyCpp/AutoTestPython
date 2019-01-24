# -*- coding: UTF8 -*-
# !/usr/bin/python

import PyQt5.QtWidgets
import PyQt5.QtCore
import PyQt5.QtGui
from . import vrSetting
from autost.api import *

class VR_Command(vrSetting.VR_Controller):
    def __init__(self, parent=None):
        super(VR_Command, self).__init__()
        self.setWindowTitle('VR Command')
        self.assistanter = parent

    def create_layout(self):
        main_layout = PyQt5.QtWidgets.QHBoxLayout()

        # key event layout
        key_layout = PyQt5.QtWidgets.QGridLayout()
        for i in range(len(self.button_names)):
            key_layout.addWidget(self.button_dict[self.button_names[i].lower()], i // 2, i % 2, 1, 1)
        key_group = PyQt5.QtWidgets.QGroupBox('Voice Command')
        key_group.setLayout(key_layout)
        main_layout.addWidget(key_group)

        self.setLayout(main_layout)
        self.setFixedWidth(int(300 * self.ratio))
        self.setFixedHeight(int(250))

    def insert_case(self, string):
        if self.assistanter:
            self.assistanter.insertText(string)
        else:
            print("assistanter pointer is nullptr")

    def key_play(self):
        filename = self.assistanter.getFilePath()
        case_list = play_wave_file(filename)
        for i in range(len(case_list)):
            self.insert_case(case_list[i])

    def key_start_siri(self):
        start_siri(self.assistanter.parent.getCaseDir())
        pass

    def key_stop_siri(self):
        case_list = stop_siri()
        for i in range(len(case_list)):
            self.insert_case(case_list[i])

    def key_start_record(self):
        case_dir = self.assistanter.getCaseDir()
        case_list = start_record(case_dir)
        for i in range(len(case_list)):
            self.insert_case(case_list[i])

    def key_stop_record(self):
        case_list = stop_record()
        for i in range(len(case_list)):
            self.insert_case(case_list[i])

    def key_volume_up(self):
        self.insert_case("keyevent(KEY_VOICE_VOLUME_UP)\n")

    def key_volume_down(self):
        self.insert_case("keyevent(KEY_VOICE_VOLUME_DOWN)\n")

    def key_voice(self):
        self.insert_case("keyevent(KEY_VOICE)\n")

