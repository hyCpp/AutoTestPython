# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-7-03

@author: wushengbing
'''
import sys
import PyQt5.QtWidgets
import PyQt5.QtCore
import PyQt5.QtGui
from win32api import GetSystemMetrics
from ui import res


SYS_WIDTH = 1280
SYS_HEIGHT = 1024

  
class CSetting(PyQt5.QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(CSetting, self).__init__()
        self.parent = parent
        self.ratio_w = GetSystemMetrics(0) / SYS_WIDTH
        self.ratio_h = GetSystemMetrics(1) / SYS_HEIGHT
        self.setWindowTitle('Setting')
        self.setWindowIcon(PyQt5.QtGui.QIcon(':/icon/setting.png'))
        self.setFixedSize(400 * self.ratio_w, 200 * self.ratio_h)
        self.initGui()
        self.createLayout()
        self.btn_ok.pressed.connect(self.changeCaptureMode)
        self.btn_cancel.pressed.connect(self.cancel)
        self.btn_ok.pressed.connect(self.changeCaseSelectMode)
        self.case_select.stateChanged.connect(self.iconUpdate)

    def initGui(self):
        self.btn_ok = PyQt5.QtWidgets.QPushButton('OK')
        self.btn_cancel = PyQt5.QtWidgets.QPushButton('Cancel')
        self.createGroupBox()
        self.createCaseSelectBox()

    def createGroupBox(self):
        self.radio_device = PyQt5.QtWidgets.QRadioButton('Device Capture')
        self.radio_screen = PyQt5.QtWidgets.QRadioButton('Screen Capture')
        self.radio_device.setIcon(PyQt5.QtGui.QIcon(':/icon/screenCapture.png'))
        self.radio_screen.setIcon(PyQt5.QtGui.QIcon(':/icon/screenCapture2.png'))
        self.group_box = PyQt5.QtWidgets.QGroupBox('Capture Mode')
        try:
            capture_mode = self.parent.captureWindow.screen.capture_mode
        except:
            capture_mode = True
        if capture_mode:
            self.radio_device.setChecked(True)
        else:
            self.radio_screen.setChecked(True)
        self.radio_layout = PyQt5.QtWidgets.QVBoxLayout()
        self.radio_layout.addWidget(self.radio_device)
        self.radio_layout.addWidget(self.radio_screen)
#        self.radio_layout.addStretch(1)
        self.group_box.setLayout(self.radio_layout)

    def createCaseSelectBox(self):
        self.case_select = PyQt5.QtWidgets.QCheckBox('Multi Case Select')
        case_mode = self.parent.caseWindow.model.multi_case_select
        self.case_select.setChecked(case_mode)
        self.group_case = PyQt5.QtWidgets.QGroupBox('Case Select Mode')
        self.case_layout = PyQt5.QtWidgets.QVBoxLayout()
        self.case_layout.addWidget(self.case_select)
        self.group_case.setLayout(self.case_layout)
        self.iconUpdate()

    def createLayout(self):
        self.layout = PyQt5.QtWidgets.QGridLayout()
        self.layout.addWidget(self.group_box, 0, 0, 2, 4)
        self.layout.addWidget(self.group_case, 4, 0, 1, 4)
        self.layout.addWidget(self.btn_ok, 5, 3, 1, 1)
        self.layout.addWidget(self.btn_cancel, 5, 4, 1, 1)
        self.setLayout(self.layout)

    def changeCaptureMode(self):
        capture_mode =  self.radio_device.isChecked()
        self.parent.captureWindow.screen.capture_mode = capture_mode
        if capture_mode:
            self.parent.action_dict['Screen Capture'].setIcon(
                                            PyQt5.QtGui.QIcon(':/icon/screenCapture.png'))
            self.parent.statusBar.showMessage('Capture Mode : Device Capture')
        else:
            self.parent.action_dict['Screen Capture'].setIcon(
                                            PyQt5.QtGui.QIcon(':/icon/screenCapture2.png'))
            self.parent.statusBar.showMessage('Capture Mode : Screen Capture')
        self.close()

    def cancel(self):
#        self.radio_device.setChecked(self.parent.captureWindow.screen.capture_mode)
        self.close()

    def changeCaseSelectMode(self):
        current_case_mode = self.parent.caseWindow.model.multi_case_select
        case_mode = self.case_select.isChecked()
        if case_mode != current_case_mode:
            self.case_select.setChecked(case_mode)
            self.parent.caseWindow.model.multi_case_select = case_mode

    def iconUpdate(self):
        case_mode = self.case_select.isChecked()
        if case_mode:
            self.case_select.setIcon(PyQt5.QtGui.QIcon(':/icon/multi.png'))
        else:
            self.case_select.setIcon(PyQt5.QtGui.QIcon(':/icon/multi2.png'))


if __name__ == '__main__':
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    w = CSetting()
    w.show()
    sys.exit(app.exec_()) 