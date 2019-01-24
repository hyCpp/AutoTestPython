# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-10-19

@author: wushengbing
'''
import sys
import os
import time
import threading
import PyQt5.QtWidgets
import PyQt5.QtGui
import PyQt5.QtCore
import autost.api
import win32gui
import win32process
import signal
from win32api import GetSystemMetrics
from pywinauto.win32functions import GetForegroundWindow
from autost.api import *
import airtest.core.android.adb as adb
from .. import res, deviceController
from . import device, setting

SYS_WIDTH = 1280



class CRadioButton(PyQt5.QtWidgets.QRadioButton):

    def __init__(self, index):
        super(CRadioButton, self).__init__()
        self.index = index

class CDeviceList(PyQt5.QtWidgets.QDockWidget):

    def __init__(self, parent=None):
        super(CDeviceList, self).__init__()
        self.setFeatures(PyQt5.QtWidgets.QDockWidget.DockWidgetClosable)
        self.setWindowTitle('Device List')
        self.ratio = GetSystemMetrics(0) / SYS_WIDTH
        self.parent = parent
        self.index = 0
#        self.checkbox_list = []
        self.uri_edit_list = []
        self.connect_btn_list = []
        self.refresh_btn_list = []
        self.radio_list = []
        self.layout_list = []
        self.initGui()
        self.createLayout()
        self.refreshADB()
        #self.createToolbar()
#        self.setContextMenuPolicy(PyQt5.QtCore.Qt.CustomContextMenu)
#        self.customContextMenuRequested.connect(self.showMenu)

    def initGui(self):
        self.radio_group = PyQt5.QtWidgets.QButtonGroup(self)
        self.radio_group.buttonToggled.connect(self.setCurrentDevice)
        self.widget = PyQt5.QtWidgets.QWidget()
        self.widget.move(PyQt5.QtCore.QPoint(0,15*self.ratio))
        self.widget.setContentsMargins(0,0,0,0)
        self.setContentsMargins(0,0,0,0)
        self.btn_style = '''
                QPushButton{background-color:rgb(180,180,180);
                            color:rgb(0,0,255);
                            text-align: center;
                            font-size: 13px;
                            border-radius: 10px;
                            border: 2px groove gray;
                            border-style: outset;}
                QPushButton:hover{border:2px rgb(255, 255, 0);
                                  border-style: outset;}
                QPushButton:pressed{background-color:rgb(240,240,240);}
        '''
        self.btn_add = PyQt5.QtWidgets.QPushButton(icon=PyQt5.QtGui.QIcon(':/icon/add.png'))
        self.btn_add.pressed.connect(self.addConnectWidget)
        self.btn_add.setFixedSize(22*self.ratio, 22*self.ratio)
        style = '''
                QPushButton{background-color:rgb(238,243,250);
                            border-radius: 10px;
                            border-style: outset;}
                QPushButton:hover{border:2px rgb(255, 255, 0);
                                  border-style: outset;}
        '''
        self.btn_add.setStyleSheet(style)
        self.createConnectWidget()

    def createToolbar(self):
        self.toolbar = PyQt5.QtWidgets.QToolBar(self)
        self.action = PyQt5.QtWidgets.QAction(PyQt5.QtGui.QIcon(':/icon/add.png'),
                                              'Add', self)
        self.action.triggered.connect(self.addConnectWidget)
        self.toolbar.addAction(self.action)
        self.toolbar.resize(25,25)

    def showMenu(self, point):
        menu = PyQt5.QtWidgets.QMenu()
        ## New
        action_name_list = ['Add', 'Delete']
        icon_list = ['add.png', 'delete2.png']
        action_connect_list = [self.addConnectWidget,
                               self.deleteRedundantConnectWidget]
        for i in range(len(action_name_list)):
            action_name = action_name_list[i]
            icon = ':/icon/%s' % icon_list[i]
            action_connect = action_connect_list[i]
            action = PyQt5.QtWidgets.QAction(PyQt5.QtGui.QIcon(icon), action_name, self)
            action.triggered.connect(action_connect)
            menu.addAction(action)
        menu.exec_(self.mapToGlobal(point))

    def switch_device(self):
        if deviceController.REC.FLAG:
            device_uri = deviceController.REC.DEVICE_URI
            if device_uri:
                func_string = "switch_device('%s')" % device_uri + os.linesep + os.linesep
                num = 15
                title = os.linesep + '#' * num + 'switch device' + '#' * num + os.linesep
                deviceController.REC.ASST.insertText(title)
                deviceController.REC.ASST.insertText(func_string)

    def setCurrentDevice(self, radio_btn, checked):
        if checked:
            try:
                self.parent.current_device.deviceToolbarUpdate.disconnect(self.parent.updateDeviceToolbar)
                self.parent.current_device.deviceWidgetRectUpdate.disconnect(self.parent.updateDeviceWidgetRect)
                self.parent.current_device.widgetShow.disconnect(self.parent.showWidget)
                self.parent.current_device.zoomFactorUpdate.disconnect(self.parent.setZoomFactor)
                self.parent.current_device.deviceWidgetOrgRectUpdate.disconnect(self.parent.updateWidgetTreeOrgRect)
                self.parent.current_device.device_proxy.widgetTreeUpdate.disconnect(self.parent.widgetTree.updateTree)
            except:
                print('Current device signal disconnect fail...')
                pass
#            self.parent.splitter_right.replaceWidget(1,self.parent.device_dict[radio_btn.index])
            self.parent.splitter_right.insertWidget(1,self.parent.device_dict[radio_btn.index])
            self.parent.splitter_right.setStretchFactor(1, 100)
            self.parent.device_dict[radio_btn.index].show()
            self.parent.device_dict[radio_btn.index].setWindowTitle('Current Device')
            deviceController.REC.DEVICE_URI = self.getCurrentURI(radio_btn.index)
            self.parent.current_device = self.parent.device_dict[radio_btn.index]
            #G.DEVICE = self.parent.device_dict[radio_btn.index].device
            #print(self.parent.device_dict)
            #for (key, value) in self.parent.device_dict.items():
            #    print(key, value)
            #switch_device(self.parent.device_dict[radio_btn.index].device.uri)
            #self.switch_device()
            try:
                self.parent.current_device.deviceToolbarUpdate.connect(self.parent.updateDeviceToolbar)
                self.parent.current_device.deviceWidgetRectUpdate.connect(self.parent.updateDeviceWidgetRect)
                self.parent.current_device.widgetShow.connect(self.parent.showWidget)
                self.parent.current_device.zoomFactorUpdate.connect(self.parent.setZoomFactor)
                self.parent.current_device.deviceWidgetOrgRectUpdate.connect(self.parent.updateWidgetTreeOrgRect)
                self.parent.current_device.device_proxy.widgetTreeUpdate.connect(self.parent.widgetTree.updateTree)
            except:
                print('Current device signal connect fail...')
                pass
        else:
#            if radio_btn.index not in [0,1]:
            self.parent.device_dict[radio_btn.index].hide()
        self.updateSize()

    def createConnectWidget(self):
        radio = CRadioButton(self.index)
        radio.setCheckable(False)
        self.index += 1
        uri_edit = PyQt5.QtWidgets.QComboBox()
        uri_edit.setDuplicatesEnabled(False)
        uri_edit.setEditable(True)
        uri_edit.lineEdit().setPlaceholderText('Please input device uri...')
        connect_btn = PyQt5.QtWidgets.QPushButton('connect')
        connect_btn.setFixedSize(75*self.ratio,22*self.ratio)
        connect_btn.setStyleSheet(self.btn_style)
        self.uri_edit_list.append(uri_edit)
        self.connect_btn_list.append(connect_btn)
        self.radio_list.append(radio)
        connect_btn.pressed.connect(self.connect)
        self.radio_group.addButton(radio)
        uri_edit.editTextChanged.connect(self.uriEditRefresh)

    def deleteRedundantConnectWidget(self):
        for i in range(len(self.connect_btn_list))[::-1]:
            if self.connect_btn_list[i] and self.connect_btn_list[i].text() == 'connect':
                if i > 0:
                    self.radio_list[i].deleteLater()
                    self.uri_edit_list[i].deleteLater()
                    self.connect_btn_list[i].deleteLater()
                    self.radio_list[i] = None
                    self.uri_edit_list[i] = None
                    self.connect_btn_list[i] = None
                    break
        self.updateSize()

    def addConnectWidget(self):
        self.createConnectWidget()
        i = len(self.uri_edit_list)
        self.layout.addWidget(self.radio_list[-1], i-1,0,1,1)
        self.layout.addWidget(self.uri_edit_list[-1], i-1,1,1,6)
        self.layout.addWidget(self.connect_btn_list[-1], i-1,7,1,2)
        self.refreshADB()
        self.updateSize()

    def deleteConnectWidget(self):
        index = self.getCurrentIndex(self.connect_btn_list)
        if index == 0:
            return
        self.radio_list[index].deleteLater()
        self.uri_edit_list[index].deleteLater()
        self.connect_btn_list[index].deleteLater()
        self.radio_list[index] = None
        self.uri_edit_list[index] = None
        self.connect_btn_list[index] = None
        self.updateSize()

    def createLayout(self):
        self.layout = PyQt5.QtWidgets.QGridLayout()
        for i in range(len(self.uri_edit_list)):
            self.layout.addWidget(self.radio_list[i], i,0,1,1)
            self.layout.addWidget(self.uri_edit_list[i], i,1,1,6)
            self.layout.addWidget(self.connect_btn_list[i], i,7,1,2)
            if i == 0:
                self.layout.addWidget(self.btn_add, i,9,1,1)
        self.layout.setColumnStretch(1, 3)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def getCurrentURI(self, index):
        t = self.uri_edit_list[index].currentText()
        return t

    def getCurrentIndex(self, widget_list):
        index = 0
        for i in range(len(widget_list)):
            if widget_list[i] and widget_list[i].isDown():
                index = i
                break
        return index

    def uriEditRefresh(self, text):
        if text == 'show more ...':
            current_edit = None
            for uri_edit in self.uri_edit_list:
                if uri_edit and uri_edit.lineEdit().text() == 'show more ...':
                    current_edit = uri_edit
                    break
            self.refreshADB()
            if current_edit:
                current_edit.showPopup()

    def clearRedundantConnectWidget(self):
        for i in range(len(self.connect_btn_list)):
            if self.connect_btn_list[i] and self.connect_btn_list[i].text() == 'connect':
                if i > 0:
                    self.radio_list[i].deleteLater()
                    self.uri_edit_list[i].deleteLater()
                    self.connect_btn_list[i].deleteLater()
                    self.radio_list[i] = None
                    self.uri_edit_list[i] = None
                    self.connect_btn_list[i] = None
        self.updateSize()

    def refreshADB(self):
        device_list = adb.ADB().devices(state='device')
        head = 'iAndroid://127.0.0.1:5037/'
        serialno_list = [head + d[0] for d in device_list]
        serialno_list += ['iauto://127.0.0.1:5391',
                          'iauto://192.168.5.111:5391',
                          'show more ...']
        for i in range(len(self.connect_btn_list)):
            if self.connect_btn_list[i]:
                text = self.connect_btn_list[i].text()
                if text == 'connect':
                    self.uri_edit_list[i].clear()
                    self.uri_edit_list[i].addItems(serialno_list)
                    self.uri_edit_list[i].setCurrentText('')

    def connect_init(self):
        index = 0
        uri_list = []
        for uri in setting.DEVICE_URI_LIST:
            if uri in uri_list:
                continue
            uri_list.append(uri)
            self.uri_edit_list[index].lineEdit().setText(uri)
            self.connect(index)
            self.addConnectWidget()
            index += 1
        else:
            self.radio_list[0].setChecked(True)

    def connect(self, index=None):
        if index is None:
            index = self.getCurrentIndex(self.connect_btn_list)
        self.uri = self.getCurrentURI(index)
        connect_text = self.connect_btn_list[index].text()
        try:
            if connect_text == 'connect':
                self.connect_device(index)
                self.uri_edit_list[index].lineEdit().setReadOnly(True)
                self.connect_btn_list[index].setText('disconnect')
                self.uri_edit_list[index].clear()
                self.uri_edit_list[index].addItem(self.uri)
            else:
                self.disconnect_device(index)
                self.uri_edit_list[index].lineEdit().setReadOnly(False)
                self.deleteConnectWidget()
                if index == 0:
                    self.connect_btn_list[index].setText('connect')
                    self.refreshADB()
        except:
            import traceback
            print(traceback.print_exc())
            return

    def connect_device(self, index=0):
        self.radio_list[index].setCheckable(True)
        if index == 0:
            self.parent.device.connect_device(self.uri)
            if len(self.parent.device_dict) == 0:
                self.parent.device.device_proxy.widgetTreeUpdate.connect(self.parent.widgetTree.updateTree)
            self.parent.device_dict[index] = self.parent.device
        else:
            new_device = device.CDeviceScreenWindow()
            new_device.connect_device(self.uri)
            self.parent.device_dict[index] = new_device
#            self.parent.splitter_right.replaceWidget(1,new_device)
            self.parent.splitter_right.insertWidget(1,new_device)
#            new_device.hide()
        self.radio_list[index].setChecked(True)
        deviceController.REC.DEVICE_NUM += 1

    def updateSize(self):
        connect_len = len([btn for btn in self.connect_btn_list if btn]) + 1
        height = round(connect_len * self.ratio * 30)
        self.setFixedHeight(height)

    def disconnect_device(self, index=0):
        if self.radio_list[index].isChecked():
            self.radio_list[0].setChecked(True)
        if hasattr(self.parent.device_dict[index], 'device_proxy'):
            try:
                self.parent.device_dict[index].device_proxy.widgetTreeUpdate.disconnect(self.parent.widgetTree.updateTree)
            except:
                pass
        self.parent.device_dict[index].disconnect_device()
        if index > 0:
            self.parent.device_dict[index].deleteLater()
            self.parent.device_dict[index] = None
        deviceController.REC.DEVICE_NUM -= 1


if __name__ == '__main__':
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    c = CDeviceList()
    c.show()
    sys.exit(app.exec_())