# -*- coding: UTF8 -*-
#!/usr/bin/python

import sys
import threading
from win32api import GetSystemMetrics
import PyQt5.QtWidgets
import PyQt5.QtCore
import PyQt5.QtGui
import sounddevice as sd
from autost.api import *
import json
import copy
import collections

SYS_WIDTH = 1200

class VR_Controller(PyQt5.QtWidgets.QDialog):
    codingupdate = PyQt5.QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(VR_Controller, self).__init__()
        self.parent = parent
        self.ratio = GetSystemMetrics(0) / SYS_WIDTH
        self.setWindowTitle('VR Setting')
        self.setWindowIcon(PyQt5.QtGui.QIcon(':/icon/tree.png'))
        self.combo_box_dict = collections.OrderedDict()
        self.button_dict = dict()
        self.device_info = dict()
        self.current_text_changed = dict()
        self.device_select = ['Microphone_Conn', 'Speaker_Conn', 'Microphone', 'Speaker']
        self.button_names = ['Start Siri', 'Stop Siri', 'Start Record', 'Stop Record', 'Play File', 'Auto Start Record'
                             , 'Select Case', 'Upload Case', 'Voice']
        self.init_device()
        self.init_ui()
        self.create_layout()
        self.codingupdate.connect(self.insertText)

    def init_device(self):
        devices = sd.query_devices()
        host_apis = sd.query_hostapis()

        serial_number = -1
        self.device_info[-1] = {"name": "", "host_api_name": "", "host_api": -1, "max_input_channels": -1, "max_output_channels": -1}
        for device in devices:
            serial_number += 1
            device_name = device["name"]
            self.device_info[serial_number] = {"name": device_name,
                                               "host_api_name": "",
                                               "host_api": device["hostapi"],
                                               "max_input_channels": device["max_input_channels"],
                                               "max_output_channels": device["max_output_channels"]}

        for host_api in host_apis:
            for index in host_api["devices"]:
                self.device_info[index]["host_api_name"] = host_api["name"]

    def init_ui(self):
        self.create_combo_box()
        self.create_buttons()
        self.create_line_edit()

    def create_combo_box(self):
        for name in self.device_select:
            self.create_one_combo_box(name)

    def create_line_edit(self):
        self.server_line_edit = PyQt5.QtWidgets.QLineEdit("192.168.64.53:9889")
        if self.parent.get_connect_status():
            self.server_button = PyQt5.QtWidgets.QPushButton('disconnect')
        else:
            self.server_button = PyQt5.QtWidgets.QPushButton('connect')

        self.server_button.setFont(PyQt5.QtGui.QFont("微软雅黑", 9))
        self.server_button.pressed.connect(self.connect_auto_test_server)

    def read_json_file(self):
        f = open("./ui/vr/vr_config.json", "r")
        json_str = f.read()
        return json.loads(json_str)

    def write_json_file(self, data):
        json_str_file = json.dumps(data, ensure_ascii=False)
        with open("./ui/vr/vr_config.json", 'w') as f:
            f.write(json_str_file)

    def get_current_combox_box_index(self, name, hostapi):
        print(name, hostapi)
        for key in self.device_info:
            if self.device_info[key]["name"] == name and self.device_info[key]["host_api"] == hostapi:
                print(self.device_info[key])
                return key
        return -1

    def create_one_combo_box(self, name):
        combo = PyQt5.QtWidgets.QComboBox()
        device_json = self.read_json_file()

        if name.find("Microphone") != -1:
            channels = "max_input_channels"
            if name.find("Conn") != -1:
                current_index = self.get_current_combox_box_index(device_json["audio_device"]["microphone_conn_machine"]["name"],
                                                                  device_json["audio_device"]["microphone_conn_machine"]["hostapi"])
            else:
                current_index = self.get_current_combox_box_index(device_json["audio_device"]["microphone"]["name"],
                                                                  device_json["audio_device"]["microphone"]["hostapi"])
        elif name.find("Speaker") != -1:
            channels = "max_output_channels"
            if name.find("Conn") != -1:
                current_index = self.get_current_combox_box_index(device_json["audio_device"]["speaker_conn_machine"]["name"],
                                                                  device_json["audio_device"]["speaker_conn_machine"]["hostapi"])
            else:
                current_index = self.get_current_combox_box_index(device_json["audio_device"]["speaker"]["name"],
                                                                  device_json["audio_device"]["speaker"]["hostapi"])
        else:
            return

        for key in self.device_info:
            if key == -1:
                combo.addItem("close")
                self.current_text_changed["close"] = key
                continue
            if self.device_info[key][channels] > 0:
                combo_text = self.device_info[key]["name"] + ", " + self.device_info[key]["host_api_name"]
                combo.addItem(combo_text)
                self.current_text_changed[combo_text] = key
        combo.setFont(PyQt5.QtGui.QFont("微软雅黑", 8))
        if current_index in self.device_info:
            if current_index == -1:
                combo.setCurrentText("close")
            else:
                combo.setCurrentText(self.device_info[current_index]["name"] + ", " + self.device_info[current_index]["host_api_name"])
                combo.setCurrentText(self.device_info[current_index]["name"] + ", " + self.device_info[current_index]["host_api_name"])
        combo.currentTextChanged[str].connect(self.get_slot_func(name))
        radio_label = PyQt5.QtWidgets.QLabel(name)
        radio_label.setFont(PyQt5.QtGui.QFont("微软雅黑", 9))
        radio_label.setStyleSheet("color:rgb(0,0,255)")

        combo_layout = PyQt5.QtWidgets.QHBoxLayout()
        combo_layout.addWidget(radio_label)
        combo_layout.addWidget(combo)

        combo_box = PyQt5.QtWidgets.QGroupBox()
        combo_box.setLayout(combo_layout)
        combo_box.setStyleSheet("border:none")
        self.combo_box_dict[name] = combo_box

    def create_buttons(self):
        style_sheet = '''
                    QPushButton{background-color:rgb(100,100,100);
                                color: white;
                                text-align: left;
                                border-radius: 10px; 
                                border: 2px groove gray;
                                border-style: outset;}

                    QPushButton:hover{border-radius: 10px;
                                    border:2px rgb(0, 255, 255);
                                    border-style: outset;}

                    QPushButton:pressed{background-color:rgb(240,240,240);}
                '''
        for name in self.button_names:
            self.create_one_button(name, style_sheet)

    def create_one_button(self, name='button', style_sheet=None):
        button = PyQt5.QtWidgets.QPushButton(PyQt5.QtGui.QIcon(":/icon/touch.png"), name)
        button.setFixedSize(160, 35)
        button.setFixedHeight(35)
        button.setFont(PyQt5.QtGui.QFont("微软雅黑", 10))
        button.setIconSize(PyQt5.QtCore.QSize(24, 24))
        if style_sheet:
            button.setStyleSheet(style_sheet)
        self.button_dict[name.lower()] = button
        button.pressed.connect(self.get_slot_func(name))

    def create_layout(self):
        # device layout
        device_layout = PyQt5.QtWidgets.QVBoxLayout()
        for key in self.combo_box_dict:
            device_layout.addWidget(self.combo_box_dict[key])
        device_group = PyQt5.QtWidgets.QGroupBox('Device')
        device_group.setFont(PyQt5.QtGui.QFont("微软雅黑", 9))
        device_group.setLayout(device_layout)
        device_group.setFixedWidth(int(350 * self.ratio))
        # device_group.setFixedHeight(int(200 * self.ratio))

        # connect layout
        server_layout = PyQt5.QtWidgets.QHBoxLayout()
        server_layout.addWidget(self.server_button)
        server_layout.addWidget(self.server_line_edit)
        server_group = PyQt5.QtWidgets.QGroupBox('Server Connect')
        server_group.setFont(PyQt5.QtGui.QFont("微软雅黑", 9))
        server_group.setLayout(server_layout)
        server_group.setFixedHeight(int(80 * self.ratio))

        # right layout
        left_layout = PyQt5.QtWidgets.QVBoxLayout()
        left_layout.addWidget(device_group)
        left_layout.addWidget(server_group)
        left_group = PyQt5.QtWidgets.QGroupBox('Settings')
        left_group.setFont(PyQt5.QtGui.QFont("微软雅黑", 9))
        left_group.setLayout(left_layout)

        # left layout
        right_layout = PyQt5.QtWidgets.QGridLayout()
        for name in self.button_names:
            right_layout.addWidget(self.button_dict[name.lower()])
        right_group = PyQt5.QtWidgets.QGroupBox('Event')
        right_group.setFont(PyQt5.QtGui.QFont("微软雅黑", 10))
        right_group.setLayout(right_layout)
        right_group.setFixedWidth(int(200 * self.ratio))

        # main layout
        main_layout = PyQt5.QtWidgets.QHBoxLayout()
        main_layout.addWidget(right_group)
        main_layout.addWidget(left_group)
        self.setLayout(main_layout)
        self.setFixedWidth(int(600 * self.ratio))

    def get_slot_func(self, name, on_off=None):
        slot_mapping = {'microphone_conn': self.vehicle_input_device,
                        'speaker_conn': self.vehicle_output_device,
                        'microphone': self.pc_input_device,
                        'speaker': self.pc_output_device,
                        'play file': self.key_play,
                        'start siri': self.key_start_siri,
                        'stop siri': self.key_stop_siri,
                        'start record': self.key_start_record,
                        'stop record': self.key_stop_record,
                        'auto start record': self.key_auto_start_record,
                        'select case': self.select_case,
                        'upload case': self.upload_case,
                        'voice': self.key_voice,
                        }
        if on_off:
            name = '_'.join([name.lower(), on_off.lower()])
        else:
            name = name.lower()
        slot_func = slot_mapping.get(name, self.default)
        return slot_func

    def insertText(self, string):
        if self.parent:
            try:
                editor = self.parent.editor.currentWidget()
                if editor:
                    try:
                        editor.scintilla.insert(string)
                        x, y = editor.scintilla.getCursorPosition()
                        editor.scintilla.setCursorPosition(x, y + len(string))
                        editor.scintilla.setFocus()
                    except:
                        editor.insertPlainText(string)
                        editor.setFocus()
            except:
                import traceback
                print(traceback.print_exc())

    def start_thread(self, func, args=()):
        t = threading.Thread(target=func, args=args)
        t.start()

    def default(self):
        print('default: this switch is not defined...')
        pass

    def connect_auto_test_server(self):
        if self.server_button.text() == 'connect':
            if self.parent.connect_vr_server(self.server_line_edit.text()):
                self.parent.set_connect_status(True)
                self.server_button.setText("disconnect")
                pop_msg_box = "Connect Success ...  "
            else:
                self.parent.set_connect_status(False)
                pop_msg_box = "Connect Fail...  "
            PyQt5.QtWidgets.QMessageBox.information(self, "warning", pop_msg_box)
        elif self.server_button.text() == 'disconnect':
            self.parent.set_connect_status(False)
            self.parent.disconnect_vr_server()
            self.server_button.setText("connect")

    def upload_case(self):
        print("upload_case")
        f = open(self.case_file_name, 'r')
        # data = f.read()
        case_dict = dict()
        case_dict["case"] = f.read()
        data = json.dumps(case_dict, ensure_ascii=False)
        if data != '':
            print(data)
            self.parent.send_data_to_server(data)

    def select_case(self):
        self.case_file_name, _ = PyQt5.QtWidgets.QFileDialog.getOpenFileName(self, 'Select Directory',
                                                                  '', 'Case File (*.py)')

    def vehicle_input_device(self, text):
        json_dict = self.read_json_file()
        if text in self.current_text_changed:
            key = self.current_text_changed[text]
            json_dict["audio_device"]["microphone_conn_machine"]["hostapi"] = self.device_info[key]["host_api"]
            json_dict["audio_device"]["microphone_conn_machine"]["name"] = self.device_info[key]["name"]
            self.write_json_file(json_dict)

    def vehicle_output_device(self, text):
        json_dict = self.read_json_file()
        if text in self.current_text_changed:
            key = self.current_text_changed[text]
            json_dict["audio_device"]["speaker_conn_machine"]["hostapi"] = self.device_info[key]["host_api"]
            json_dict["audio_device"]["speaker_conn_machine"]["name"] = self.device_info[key]["name"]
            self.write_json_file(json_dict)

    def pc_output_device(self, text):
        json_dict = self.read_json_file()
        if text in self.current_text_changed:
            key = self.current_text_changed[text]
            json_dict["audio_device"]["speaker"]["hostapi"] = self.device_info[key]["host_api"]
            json_dict["audio_device"]["speaker"]["name"] = self.device_info[key]["name"]
            self.write_json_file(json_dict)

    def pc_input_device(self, text):
        json_dict = self.read_json_file()
        if text in self.current_text_changed:
            key = self.current_text_changed[text]
            json_dict["audio_device"]["microphone"]["hostapi"] = self.device_info[key]["host_api"]
            json_dict["audio_device"]["microphone"]["name"] = self.device_info[key]["name"]
            self.write_json_file(json_dict)

    def getFilePath(self):
        filename, _ = PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,
                                                                  'Open Audio File',
                                                                   "", "audio(*.wav)")
        filename = filename.split('/')[-1]
        return filename

    def key_play(self):
        filename = self.getFilePath()
        case_list = play_wave_file(filename)
        for i in range(len(case_list)):
            self.insertText(case_list[i])

    def key_start_siri(self):
        start_siri(self.parent.getCaseDir())

    def key_stop_siri(self):
        case_list = stop_siri()
        for i in range(len(case_list)):
            self.insertText(case_list[i])

    def key_start_record(self):
        case_dir = self.getCaseDir()
        case_list = start_record(case_dir)
        for i in range(len(case_list)):
            self.insertText(case_list[i])

    def key_stop_record(self):
        case_list = stop_record()
        for i in range(len(case_list)):
            self.insertText(case_list[i])

    def key_voice(self):
        self.insertText("keyevent(KEY_VOICE)\n")
        self.start_thread(keyevent, (KEY_VOICE,))

    def key_auto_start_record(self):
        def case_list_call_back(case):
            self.codingupdate.emit(case)
            pass
        filename, _ = PyQt5.QtWidgets.QFileDialog.getOpenFileName(self, 'Open Audio File', "", "")

        start_play_file_list(filename, case_list_call_back)

if __name__ == '__main__':
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    w = VR_Controller()
    w.show()
    sys.exit(app.exec_())

