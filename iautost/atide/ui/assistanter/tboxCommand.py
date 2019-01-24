# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-10-26

@author: wushengbing
'''
import PyQt5.QtWidgets
import PyQt5.QtCore
import PyQt5.QtGui
from ui import deviceController


class CTboxCommand(deviceController.CDeviceController):
    '''
        autocoding Tbox command...
    '''
    def __init__(self, parent=None):
        super(CTboxCommand, self).__init__()
        self.setWindowTitle('Tbox')
        self.parent = parent

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
        tbox_group.setFixedWidth(int(170*self.ratio))
        usb_group.setFixedWidth(int(170*self.ratio))
        self.setFixedWidth(int(400*self.ratio))
        device_group = PyQt5.QtWidgets.QGroupBox('Tbox')
        device_layout = PyQt5.QtWidgets.QHBoxLayout()
        device_layout.addWidget(tbox_group)
        device_layout.addWidget(usb_group)
        device_group.setLayout(device_layout)
        self.layout.addWidget(device_group)
        self.setLayout(self.layout)

    def insertText(self, string):
        if self.parent:
            self.parent.insertText(string + '\n')

    def acc_on(self):
        if self.group_box_dict['ACC']['ON'].isChecked():
            cmd = 'acc_on()'
            self.insertText(cmd)
            self.close()

    def acc_off(self):
        if self.group_box_dict['ACC']['OFF'].isChecked():
            cmd = 'acc_off()'
            self.insertText(cmd)
            self.close()

    def bup_on(self):
        if self.group_box_dict['B+']['ON'].isChecked():
            cmd = 'bup_on()'
            self.insertText(cmd)
            self.close()

    def bup_off(self):
        if self.group_box_dict['B+']['OFF'].isChecked():
            cmd = 'bup_off()'
            self.insertText(cmd)
            self.close()

    def rev_on(self):
        if self.group_box_dict['REV']['ON'].isChecked():
            cmd = 'rev_on()'
            self.insertText(cmd)
            self.close()

    def rev_off(self):
        if self.group_box_dict['REV']['OFF'].isChecked():
            cmd = 'rev_off()'
            self.insertText(cmd)
            self.close()

    def ig_on(self):
        if self.group_box_dict['IG']['ON'].isChecked():
            cmd = 'ig_on()'
            self.insertText(cmd)
            self.close()
            
    def ig_off(self):
        if self.group_box_dict['IG']['OFF'].isChecked():
            cmd = 'ig_off()'
            self.insertText(cmd)
            self.close()

    def ill_up_on(self):
        if self.group_box_dict['ILL+']['ON'].isChecked():
            cmd = 'ill_on()'
            self.insertText(cmd)
            self.close()
            
    def ill_up_off(self):
        if self.group_box_dict['ILL+']['OFF'].isChecked():
            cmd = 'ill_off()'
            self.insertText(cmd)
            self.close()

    def pkb_on(self):
        if self.group_box_dict['PKB']['ON'].isChecked():
            cmd = 'pkb_on()'
            self.insertText(cmd)
            self.close()

    def pkb_off(self):
        if self.group_box_dict['PKB']['OFF'].isChecked():
            cmd = 'pkb_off()'
            self.insertText(cmd)
            self.close()                  

    def usb_on(self, usb_port):
        cmd = 'usb_on(%s)' % usb_port
        self.insertText(cmd)
        self.close() 

    def usb_off(self, usb_port):
        cmd = 'usb_off(%s)' % usb_port
        self.insertText(cmd)
        self.close() 

    def usba_on(self):
        self.usb_on(1)

    def usba_off(self):
        self.usb_off(1)

    def usbb_on(self):
        self.usb_on(2)

    def usbb_off(self):
        self.usb_off(2)

    def usbc_on(self):
        self.usb_on(3)

    def usbc_off(self):
        self.usb_off(3)

    def usb1_on(self):
        self.usb_on(4)

    def usb1_off(self):
        self.usb_off(4)

    def usb2_on(self):
        self.usb_on(5)

    def usb2_off(self):
        self.usb_off(5)

    def usb3_on(self):
        self.usb_on(6)

    def usb3_off(self):
        self.usb_off(6)

    def usb4_on(self):
        self.usb_on(7)

    def usb4_off(self):
        self.usb_off(7)

    def setSpeed(self):
        speed = self.speed_slider.value()
        cmd = 'spd_speed(%s)' % speed
        self.insertText(cmd)
        self.close()

    def ill_down(self):
        hz = self.ill_hz.value()
        val = self.ill_val.value()
        cmd = 'ill_down(%s, %s)' % (hz, val)
        self.insertText(cmd)
        self.close()     
