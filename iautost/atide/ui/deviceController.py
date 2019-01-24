# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-8-21

@author: wushengbing
'''
import os
import sys
import time
import threading
from win32api import GetSystemMetrics
import PyQt5.QtWidgets
import PyQt5.QtCore
import PyQt5.QtGui
from autost.api import *
from . import res

SpinBox_WIDTH = 80
SpinBox_HEIGHT = 25
SYS_WIDTH = 1280


class REC(object):
    """
        global parameters of record...
    """
    ASST = None
    FLAG = False
    DEVICE_URI = None
    DEVICE_NUM = 0
    DEVICE_URI_MAPPING = {}


def record(f):
    def getFunction(args):
        try:
            if type(args[2][0]) == type(()):
                paras = str(args[2][0][0])
            else:
                paras = str(args[2][0])
            try:
                p = ','.join([str(a) for a in args[2][1:]])
                if p:
                    paras += ',' + p
            except:
                pass
        except:
            paras = ''
        func_name = args[1].__name__
        if func_name == 'keyevent':
            if REC.DEVICE_NUM > 1:
                paras += ", device=%s" % REC.DEVICE_URI_MAPPING.get(REC.DEVICE_URI)
        paras = '(' + paras + ')'
        function = func_name + paras + os.linesep
        return function

    def func(*args):
        try:
            try:
                r = f(*args)
            except:
                r = f(args[0])
            if REC.FLAG:
                REC.ASST.insertText(getFunction(args))
                try:
                    REC.ASST.parent.editor.currentWidget().moveScrollToEnd()
                except:
                    pass
        except:
            import traceback
            print(traceback.print_exc())
            return None
        return r
    return func


class CDeviceController(PyQt5.QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(CDeviceController, self).__init__()
        self.parent = parent
        self.ratio = GetSystemMetrics(0) / SYS_WIDTH
        self.setWindowTitle('Device Controller')
        self.setWindowIcon(PyQt5.QtGui.QIcon(':/icon/tbox.png'))
        self.group_box_dict = {}
        self.button_dict = {}
        self.initGui()
        self.createLayout()

    def initGui(self):
        self.createGroupBox()
        self.createButtons()
        self.createSPD()
        self.createILL()

    def createSPD(self):
        self.speed = PyQt5.QtWidgets.QSpinBox()
        self.speed_slider = PyQt5.QtWidgets.QSlider(PyQt5.QtCore.Qt.Horizontal)
        self.speed.setRange(0,255)
        self.speed_slider.setRange(0,255)
        self.speed.setValue(0)
        self.speed_slider.setValue(0)
        self.speed.setSingleStep(1)
        self.speed_slider.setSingleStep(1)
        self.speed.setSuffix(' km/h')
        self.speed.setFixedSize(SpinBox_WIDTH,SpinBox_HEIGHT)
        self.speed_slider.setFixedSize(SpinBox_WIDTH,SpinBox_HEIGHT)
        self.speed_btn = PyQt5.QtWidgets.QPushButton('SPD')
        self.speed_btn.setFixedSize(28,28)
        self.btn_style = '''
                   QPushButton{background-color:rgb(180,180,180);
                            color:rgb(0,0,255);
                            text-align: center;
                            border-radius: 12px;
                            border: 2px groove gray;
                            border-style: outset;}
                QPushButton:hover{border:2px rgb(255, 255, 0);
                                  border-style: outset;}
                QPushButton:pressed{background-color:rgb(240,240,240);}
        '''
        self.speed_btn.setStyleSheet(self.btn_style)
        self.speed_layout = PyQt5.QtWidgets.QHBoxLayout()
        para_layout = PyQt5.QtWidgets.QVBoxLayout()
        para_layout.addWidget(self.speed)
        para_layout.addWidget(self.speed_slider)
        self.speed_layout.addWidget(self.speed_btn)
        self.speed_layout.addLayout(para_layout)
        self.speed_group_box = PyQt5.QtWidgets.QGroupBox()
        self.speed_group_box.setLayout(self.speed_layout)
#        self.speed_group_box.setStyleSheet("QGroupBox{border:none;}")
        self.speed.valueChanged.connect(self.speed_slider.setValue)
        self.speed_slider.valueChanged.connect(self.speed.setValue)
        self.speed_btn.pressed.connect(self.setSpeed)

    def createILL(self):
        self.ill_hz = PyQt5.QtWidgets.QSpinBox()
        self.ill_val = PyQt5.QtWidgets.QSpinBox()
        self.ill_hz.setRange(126,166)
        self.ill_val.setRange(0,100)
        self.ill_hz.setSuffix(' Hz')
        self.ill_val.setSuffix(' val')
        self.ill_hz.setValue(126)
        self.ill_val.setValue(0)
        self.ill_btn = PyQt5.QtWidgets.QPushButton('ILL-')
        self.ill_btn.setFixedSize(28,28)
        self.ill_btn.setStyleSheet(self.btn_style)
        self.ill_hz.setFixedSize(SpinBox_WIDTH,SpinBox_HEIGHT)
        self.ill_val.setFixedSize(SpinBox_WIDTH,SpinBox_HEIGHT)
        self.ill_layout = PyQt5.QtWidgets.QHBoxLayout()
        para_layout = PyQt5.QtWidgets.QVBoxLayout()
        para_layout.addWidget(self.ill_hz)
        para_layout.addWidget(self.ill_val)
        self.ill_layout.addWidget(self.ill_btn)
        self.ill_layout.addLayout(para_layout)
        self.ill_group_box = PyQt5.QtWidgets.QGroupBox()
        self.ill_group_box.setLayout(self.ill_layout)
#        self.ill_group_box.setStyleSheet("QGroupBox{border:none;}")
        self.ill_btn.pressed.connect(self.ill_down)

    def createOneButton(self, name='button', style_sheet=None):
        button = PyQt5.QtWidgets.QPushButton(name)
        button.setFixedSize(80,28)
        if style_sheet:
            button.setStyleSheet(style_sheet)
        self.button_dict[name.lower()] = button
        button.pressed.connect(self.getSlot(name))

    def createOneGroupBox(self, name):
        on = PyQt5.QtWidgets.QRadioButton('ON')
        off = PyQt5.QtWidgets.QRadioButton('OFF')
        group_box = PyQt5.QtWidgets.QGroupBox()
#        group_box.setAlignment(PyQt5.QtCore.Qt.AlignLeft)
        off.setChecked(False)
        on.setChecked(False)
        radio_label = PyQt5.QtWidgets.QLabel(name)
        radio_label.setStyleSheet("color:rgb(0,0,255)")
        radio_layout = PyQt5.QtWidgets.QHBoxLayout()
        radio_layout.addWidget(radio_label)
        radio_layout.addWidget(on)
        radio_layout.addWidget(off)
        group_box.setLayout(radio_layout)
        self.group_box_dict[name] = {'ON':on, 'OFF':off, 'group_box':group_box}
#        on.toggled.connect(self.getSlot(name, 'ON'))
#        off.toggled.connect(self.getSlot(name, 'OFF'))
        on.clicked.connect(self.getSlot(name, 'ON'))
        off.clicked.connect(self.getSlot(name, 'OFF'))
        group_box.setStyleSheet("border:none")

    def createGroupBox(self):
        self.switch_names = ['B+', 'ACC', 'IG', 'REV', 'PKB', 'ILL+',
                            'USB-A','USB-B','USB-C', 'USB-1','USB-2','USB-3','USB-4']
        for name in self.switch_names:
            self.createOneGroupBox(name)

    def createButtons(self):#rgb(33,100,160)
        style_sheet = '''
                QPushButton{background-color:rgb(180,180,180);
                            color:rgb(0,0,200);
                            font-size: 13px;
                            text-align: center;
                            border-radius: 8px;
                            border: 2px groove gray;
                            border-style: outset;}

                QPushButton:hover{border:2px rgb(255, 255, 0);
                                  border-style: outset;}

                QPushButton:pressed{background-color:rgb(240,240,240);}
            '''
        self.button_names = ['Home', 'Seek', 'Menu', 'Track', 'Audio', 'Phone',
                             'Map', 'Apps', 'Volume +', 'Tune +', 'Volume -','Tune -']
        for name in self.button_names:
            self.createOneButton(name, style_sheet)

    def createLayout(self):
        self.layout = PyQt5.QtWidgets.QHBoxLayout()
        self.tbox_layout =  PyQt5.QtWidgets.QVBoxLayout()
        self.usb_layout = PyQt5.QtWidgets.QVBoxLayout()
        tbox_keys = [name for name in self.switch_names if not name.startswith('USB')]
        usb_keys = [name for name in self.switch_names if name.startswith('USB')]
        for key in tbox_keys:
            self.tbox_layout.addWidget(self.group_box_dict[key]['group_box'])
        self.tbox_layout.addWidget(self.ill_group_box)
        self.tbox_layout.addWidget(self.speed_group_box)
        tbox_group = PyQt5.QtWidgets.QGroupBox()
        tbox_group.setLayout(self.tbox_layout)
        for key in usb_keys:
            self.usb_layout.addWidget(self.group_box_dict[key]['group_box'])
        usb_group = PyQt5.QtWidgets.QGroupBox()
        usb_group.setLayout(self.usb_layout)
        self.key_layout = PyQt5.QtWidgets.QGridLayout()
        for i in range(len(self.button_names)):
            self.key_layout.addWidget(self.button_dict[self.button_names[i].lower()], i // 2, i % 2, 1, 1)
        key_group = PyQt5.QtWidgets.QGroupBox('Keyevent')
        key_group.setLayout(self.key_layout)
        key_group.setFixedWidth(int(200*self.ratio))
        tbox_group.setFixedWidth(int(170*self.ratio))
        usb_group.setFixedWidth(int(170*self.ratio))
        self.setFixedWidth(int(600*self.ratio))
        device_group = PyQt5.QtWidgets.QGroupBox('Tbox')
        device_layout = PyQt5.QtWidgets.QHBoxLayout()
        device_layout.addWidget(tbox_group)
        device_layout.addWidget(usb_group)
        device_group.setLayout(device_layout)
        self.layout.addWidget(device_group)
        self.layout.addWidget(key_group)
        self.setLayout(self.layout)

    def default(self):
        print('---------------default---------------: this switch is not defined...')
        pass

    def acc_on(self):
        if self.group_box_dict['ACC']['ON'].isChecked():
            self.startThread(acc_on)

    def acc_off(self):
        if self.group_box_dict['ACC']['OFF'].isChecked():
            self.startThread(acc_off)

    def bup_on(self):
        if self.group_box_dict['B+']['ON'].isChecked():
            self.startThread(bup_on)

    def bup_off(self):
        if self.group_box_dict['B+']['OFF'].isChecked():
            self.startThread(bup_off)

    def rev_on(self):
        if self.group_box_dict['REV']['ON'].isChecked():
            self.startThread(rev_on)

    def rev_off(self):
        if self.group_box_dict['REV']['OFF'].isChecked():
            self.startThread(rev_off)

    def ig_on(self):
        if self.group_box_dict['IG']['ON'].isChecked():
            self.startThread(ig_on)

    def ig_off(self):
        if self.group_box_dict['IG']['OFF'].isChecked():
            self.startThread(ig_off)

    def ill_up_on(self):
        if self.group_box_dict['ILL+']['ON'].isChecked():
            self.startThread(ill_on)

    def ill_up_off(self):
        if self.group_box_dict['ILL+']['OFF'].isChecked():
            self.startThread(ill_off)

    def pkb_on(self):
        if self.group_box_dict['PKB']['ON'].isChecked():
            self.startThread(pkb_on)

    def pkb_off(self):
        if self.group_box_dict['PKB']['OFF'].isChecked():
            self.startThread(pkb_off)

    def keyevent(self, keyname):
        keyevent(keyname, device=REC.DEVICE_URI)

    def key_home(self):
        self.startThread(self.keyevent, ('HOME',))

    def key_menu(self):
        self.startThread(self.keyevent, ('MENU',))

    def key_volume_up(self):
        self.startThread(self.keyevent, ('VOLUME_UP',))

    def key_volume_down(self):
        self.startThread(self.keyevent, ('VOLUME_DOWN',))

    def key_audio(self):
        self.startThread(self.keyevent, ('AUDIO',))

    def key_map(self):
        self.startThread(self.keyevent, ('MAP',))

    def key_seek(self):
        self.startThread(self.keyevent, ('SEEK',))

    def key_track(self):
        self.startThread(self.keyevent, ('TRACK',))

    def key_phone(self):
        self.startThread(self.keyevent, ('PHONE',))

    def key_apps(self):
        self.startThread(self.keyevent, ('APPS',))

    def key_tune_down(self):
        self.startThread(self.keyevent, ('TUNE_DOWN',))

    def key_tune_up(self):
        self.startThread(self.keyevent, ('TUNE_UP',))

    def usba_on(self):
        self.startThread(usb_on, (1,))

    def usba_off(self):
        self.startThread(usb_off, (1,))

    def usbb_on(self):
        self.startThread(usb_on, (2,))

    def usbb_off(self):
        self.startThread(usb_off, (2,))

    def usbc_on(self):
        self.startThread(usb_on, (3,))

    def usbc_off(self):
        self.startThread(usb_off, (3,))

    def usb1_on(self):
        self.startThread(usb_on, (4,))

    def usb1_off(self):
        self.startThread(usb_off, (4,))

    def usb2_on(self):
        self.startThread(usb_on, (5,))

    def usb2_off(self):
        self.startThread(usb_off, (5,))

    def usb3_on(self):
        self.startThread(usb_on, (6,))

    def usb3_off(self):
        self.startThread(usb_off, (6,))

    def usb4_on(self):
        self.startThread(usb_on, (7,))

    def usb4_off(self):
        self.startThread(usb_off, (7,))

    @record
    def startThread(self, func, args=()):
        t = threading.Thread(target=func, args=args)
        t.start()

    def setSpeed(self):
        speed = self.speed_slider.value()
        self.startThread(spd_speed, (speed,))

    def ill_down(self):
        para1 = self.ill_hz.value()
        para2 = self.ill_val.value()
        self.startThread(ill_down, (para1,para2))

    def getSlot(self, name, on_off=None):
        slot_mapping = {'b+_on': self.bup_on,
                        'b+_off': self.bup_off,
                        'acc_on': self.acc_on,
                        'acc_off': self.acc_off,
                        'ig_on': self.ig_on,
                        'ig_off': self.ig_off,
                        'ill+_on': self.ill_up_on,
                        'ill+_off': self.ill_up_off,
                        'rev_on': self.rev_on,
                        'rev_off': self.rev_off,
                        'pkb_on': self.pkb_on,
                        'pkb_off': self.pkb_off,
                        'usb-a_on': self.usba_on,
                        'usb-a_off': self.usba_off,
                        'usb-b_on': self.usbb_on,
                        'usb-b_off': self.usbb_off,
                        'usb-c_on': self.usbc_on,
                        'usb-c_off': self.usbc_off,
                        'usb-1_on': self.usb1_on,
                        'usb-1_off': self.usb1_off,
                        'usb-2_on': self.usb2_on,
                        'usb-2_off': self.usb2_off,
                        'usb-3_on': self.usb3_on,
                        'usb-3_off': self.usb3_off,
                        'usb-4_on': self.usb4_on,
                        'usb-4_off': self.usb4_off,
                        'home': self.key_home,
                        'menu': self.key_menu,
                        'volume +': self.key_volume_up,
                        'volume -': self.key_volume_down,
                        'audio': self.key_audio,
                        'map': self.key_map,
                        'seek': self.key_seek,
                        'track': self.key_track,
                        'phone': self.key_phone,
                        'apps': self.key_apps,
                        'tune +': self.key_tune_up,
                        'tune -': self.key_tune_down
                        }
        if on_off:
            name = '_'.join([name.lower(), on_off.lower()])
        else:
            name = name.lower()
        slot_func = slot_mapping.get(name, self.default)
        return slot_func


if __name__ == '__main__':
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    w = CDeviceController()
    w.show()
    sys.exit(app.exec_()) 