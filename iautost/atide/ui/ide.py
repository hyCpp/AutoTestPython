# -*- coding: utf-8 -*-
import sys
import time
import threading
import os
import re
import copy
import json
import shutil
import subprocess
import PyQt5.QtWidgets
import PyQt5.QtGui
import PyQt5.QtCore
from win32api import GetSystemMetrics
from PIL import Image, ImageGrab
from ui.device import device, deviceList
from ui.caseManager import caseManager, multiRunConfig, caseAttributesSetting
from ui.editor import editor, htmlParser
from ui.widgetTree import widgetTree, widgetInfo, treeFinder
from ui.screenCapture import screenCapture
from ui.common import defaultWindow
from ui.common.traceback import trace
from . import deviceController, res, shell, help
from ui.setting import setting
from ui.assistanter import assistanter
from ui.vr import vrSetting, autoTestClient
import autost.api

TEMPLATE ="Template('%s')"


class EmittingStream(PyQt5.QtCore.QObject):
    textWritten = PyQt5.QtCore.pyqtSignal(str)
    
    def write(self, text):
        self.textWritten.emit(str(text))
    
    def flush(self):
        pass
    
    def fileno(self):
        return 1


class CIDEWindow(PyQt5.QtWidgets.QMainWindow):

    def __init__(self):
        super(CIDEWindow, self).__init__()
        self.system_width = GetSystemMetrics(0)
        self.system_height = GetSystemMetrics(1)
        self.initUI()
        #sys.stdout = EmittingStream(textWritten=self.simpleOutput)
        #sys.stderr = EmittingStream(textWritten=self.simpleOutput)
        self.setMouseTracking(False)
        self.capture_file = None
        self.loadHistory()
        self.updateToolbar()
        self.case_run_proc = []
        self.connect_flag = False
        self.rec_flag = False
        self.ctrl_alt_flag = 0
        self.connect_status = False
        self.device_dict = {}
        self.current_device = self.device
        self.vr_client = autoTestClient.VrClient(self)

    def __del__(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
    def initUI(self):
        self.setWindowTitle('AutoTest')
        self.setWindowIcon(PyQt5.QtGui.QIcon(':/icon/iauto.png'))
        self.statusBar = self.statusBar()
        ##device screen
        self.device = device.CDeviceScreenWindow()
        self.device.deviceToolbarUpdate.connect(self.updateDeviceToolbar)
        self.device.deviceWidgetRectUpdate.connect(self.updateDeviceWidgetRect)
        self.device.widgetShow.connect(self.showWidget)
        self.device.zoomFactorUpdate.connect(self.setZoomFactor)
        self.device.deviceWidgetOrgRectUpdate.connect(self.updateWidgetTreeOrgRect)
        ##code editor
        self.editor = editor.CMultiEditor()
        self.editor.statusBarMessageShow.connect(self.statusBar.showMessage)
        self.editor.toolbarUpdate.connect(self.updateToolbar)
        self.editor.currentChanged.connect(self.updateToolbar)
        ##log show
        self.shell = shell.CShell()
        self.shell.stopRun.connect(self.stop)
        ##case manager
        self.caseWindow = caseManager.CCaseManager()
        self.caseManager = self.caseWindow.splitter
        self.caseWindow.fileOpen.connect(self.openFile)
        self.caseWindow.captureInsert.connect(self.InsertAsCapture)
        self.caseWindow.caseManagerDelete.connect(self.caseManagerDelete)
        self.caseWindow.caseRun.connect(self.caseManagerRun)
        self.caseWindow.multiCaseRun.connect(self.caseManagerMultiRun)
        self.caseWindow.model.dataChanged.connect(self.caseManagerDataChange)
        ##widget tree
        self.widgetTree = widgetTree.CWidgetTree()
        self.widgetTree.deviceToolbarUpdate.connect(self.updateDeviceToolbar)
        self.widgetTree.screenSizeSet.connect(self.setScreenSize)
        self.widgetTree.propertiesShow.connect(self.showWidgetProperties)
        self.widgetTree.widgetShow.connect(self.showWidgetFromItem)
        ##widget information
        self.widgetInfo = widgetInfo.CWidgetInfo()
        ##
        ##screen capture
        self.captureWindow = screenCapture.CCaptureWindow()
        self.captureWindow.screen.autoCoding.connect(self.autoCoding)
        self.captureWindow.screen.statusBarMsg.connect(self.statusBar.showMessage)
        self.captureWindow.screen.caseWindowFileRefresh.connect(self.caseWindow.newFileRefresh)
        self.captureWindow.screen.toolBarUpdate.connect(self.updateToolbar)
        self.captureWindow.toolBarUpdate.connect(self.updateToolbar)
        ##
        ## api code assistanter
        self.assistanter = assistanter.CAssistanter(self)
        self.assistanter.hide()
        ## device connect
        self.deviceList = deviceList.CDeviceList(self)

        self.deviceList.hide()
        self.action_dict = {}
        self.__createMenu()
        self.__createToolBar()
        self.__createLayout()

    def __createLayout(self):
        self.splitter_main = PyQt5.QtWidgets.QSplitter(PyQt5.QtCore.Qt.Horizontal)
        self.setCentralWidget(self.splitter_main)
        self.splitter_main.resize(self.system_width, self.system_height)
        splitter_left = PyQt5.QtWidgets.QSplitter(PyQt5.QtCore.Qt.Vertical)
        self.splitter_center = PyQt5.QtWidgets.QSplitter(PyQt5.QtCore.Qt.Vertical)
        splitter_right = PyQt5.QtWidgets.QSplitter(PyQt5.QtCore.Qt.Vertical)
        self.splitter_main.addWidget(splitter_left)
        self.splitter_main.addWidget(self.splitter_center)
        self.splitter_main.addWidget(splitter_right)
        self.splitter_main.setContentsMargins(2, 2, 2, 0)
        splitter_left.resize(self.system_width * 1/9, self.system_height)
        splitter_left.addWidget(self.caseManager)
        splitter_left.setCollapsible(0, False)
        self.splitter_center.resize(self.system_width * 4/9, self.system_height)
        splitter_right.resize(self.system_width * 4/9, self.system_height)
        splitter_editor = PyQt5.QtWidgets.QSplitter(PyQt5.QtCore.Qt.Horizontal)
        splitter_editor.addWidget(self.editor)
        splitter_editor.addWidget(self.assistanter)
        splitter_editor.resize(self.splitter_center.width(), self.splitter_center.height() * 0.618)
        splitter_editor.handle(1).setDisabled(True)
        self.splitter_center.addWidget(splitter_editor)
        self.splitter_center.addWidget(self.shell)
        self.splitter_center.setCollapsible(0, False)
        self.splitter_center.setCollapsible(1, False)
        self.shell.resize(self.splitter_center.width(), self.splitter_center.height() * 0.382)
        splitter_right_bottom = PyQt5.QtWidgets.QSplitter(PyQt5.QtCore.Qt.Horizontal)
        splitter_right.addWidget(self.deviceList)
        splitter_right.addWidget(self.device)
        splitter_right.addWidget(splitter_right_bottom)
        splitter_right.setCollapsible(0, False)
        splitter_right.setCollapsible(1, False)
        #splitter_right.setCollapsible(2, False)
        self.splitter_right = splitter_right
        self.device.resize(splitter_right.width(), splitter_right.height() * 0.618)
        splitter_right_bottom.resize(splitter_right.width(), splitter_right.height() * 0.382)
        self.widgetTree.resize(splitter_right_bottom.width()/2, splitter_right_bottom.height())
        self.widgetInfo.resize(splitter_right_bottom.width()/2, splitter_right_bottom.height())
        splitter_right_bottom.addWidget(self.widgetTree)
        splitter_right_bottom.addWidget(self.widgetInfo)
        splitter_right_bottom.setCollapsible(0, False)
        splitter_right_bottom.setCollapsible(1, False)
        self.splitter_main.setCollapsible(0, False)
        self.splitter_main.setCollapsible(1, False)
        self.splitter_main.setCollapsible(2, False)

    def normalOutputWritten(self, text):
        if self.isVisible():
            t = text.split('\n')
            text = '\n   '.join(t)
            text = '\n>>> ' + text
            cursor = self.shell.edit.textCursor()
            cursor.movePosition(PyQt5.QtGui.QTextCursor.End)
            cursor.insertText(text)
            self.shell.edit.setTextCursor(cursor)
            self.shell.edit.ensureCursorVisible()

    def simpleOutput(self, text):
        if self.isVisible():
            cursor = self.shell.edit.textCursor()
            line_count = self.shell.edit.document().lineCount() - 100
            if line_count > 0:
                cursor.setPosition(0)
                cursor.movePosition(PyQt5.QtGui.QTextCursor.Down,
                                    PyQt5.QtGui.QTextCursor.KeepAnchor,
                                    line_count)
                cursor.removeSelectedText()
            cursor.movePosition(PyQt5.QtGui.QTextCursor.End)
            cursor.insertText(text)
            scrollbar = self.shell.edit.verticalScrollBar()
            scrollbar.setSliderPosition(scrollbar.maximum())
            self.shell.edit.repaint()

    def __createMenu(self):
        self.toolbar_info = {}
        self.toolbar_default_name_list = ['Save',
                                          'Save All',
                                          'Save As',
                                          'Change Editor',
                                          'Run','Setting',
                                          'Record Mode',
                                          'Assistanter',
                                          'Find Widget',
                                          'Device Controller',
                                          'Device Connect',
                                          'Voice Setting']
        self.toolbar_name_list = copy.deepcopy(self.toolbar_default_name_list)
        menubar = self.menuBar()  
        fileMenu = menubar.addMenu('File')
        newMenu = fileMenu.addMenu('New')
        fileMenu.addSeparator()
        action_name_list = ['New Case', 'New File']
        action_connect_list = [self.__newCase, self.__newFile]
        self.__addAction(menu=newMenu,
                         action_name_list=action_name_list,
                         action_connect_list=action_connect_list)
        action_name_list = ['Open File', 'Save', 'Save All', 'Save As']
        action_connect_list = [self.openFile, self.__saveFile,
                               self.__saveAllFile, self.__saveFileAs]
        icon_list = ['open.png', 'save.png','saveAll.png', 'saveAs.png']
        short_cut_list = ['Ctrl+O', 'Ctrl+S', 'Ctrl+Shift+S', None]
        separetor_list = [True, False, False, False]
        self.toolbar_info['file'] = {'action_name_list':action_name_list,
                                     'action_connect_list':action_connect_list,
                                     'icon_list':icon_list,
                                     'short_cut_list':short_cut_list,
                                     'separetor_list':separetor_list}
        self.__addAction(menu=fileMenu,
                         action_name_list=action_name_list,
                         action_connect_list=action_connect_list,
                         icon_list=icon_list,
                         short_cut_list=short_cut_list,
                         separetor_list=separetor_list)

        ##Edit menu
        editMenu = menubar.addMenu('Edit')
        action_name_list = ['Change Editor','Run','Setting']
        action_connect_list = [self.changeEditor,self.__runOne,self.__setting]
        icon_list = ['change.png','run.png','setting.png']
        separetor_list = [True, True, False]
        short_cut_list = ['Ctrl+Shift+C', None, None]
        self.__addAction(menu=editMenu,
                         action_name_list=action_name_list,
                         action_connect_list=action_connect_list,
                         icon_list=icon_list,
                         short_cut_list=short_cut_list,
                         separetor_list=separetor_list)
        self.toolbar_info['edit'] = {'action_name_list':action_name_list,
                                     'action_connect_list':action_connect_list,
                                     'icon_list':icon_list,
                                     'short_cut_list':short_cut_list,
                                     'separetor_list':separetor_list}

        ##Tools menu
        editMenu = menubar.addMenu('Tools')
        action_name_list = ['Record Mode', 'Assistanter','Screen Capture',
                            'Find Widget','Device Controller','Device Connect',
                            'Voice Setting']
        action_connect_list = [self.setRecMode,self.showAssistanter,self.screenCapture,
                               self.findWidget, self.deviceController, self.showDeviceConnect,
                               self.voiceSetting]
        icon_list = ['rec.png','assistanter.png','screenCapture.png','find.png','tbox.png','connect.png', 'tree.png']
        short_cut_list = [None, None, 'Ctrl+Alt+C', None, None, None]
        self.__addAction(menu=editMenu,
                         action_name_list=action_name_list,
                         action_connect_list=action_connect_list,
                         icon_list=icon_list,
                         short_cut_list=short_cut_list)
        self.toolbar_info['tools'] = {'action_name_list':action_name_list,
                                     'action_connect_list':action_connect_list,
                                     'icon_list':icon_list,
                                     'short_cut_list':short_cut_list}

        ##view menu
        viewMenu = menubar.addMenu('View')
        toolMenu = viewMenu.addMenu('Toolbars')
        action = PyQt5.QtWidgets.QAction(PyQt5.QtGui.QIcon(':/icon/default_toolbar.png'), 'Default Toolbar', self)
        action.triggered.connect(self.setDefaultToolbar)
        toolMenu.addAction(action)
        toolMenu.addSeparator()
        self.toolbar_action_dict = {}
        for menu_name in ['file', 'edit', 'tools']:
            action_name_list = self.toolbar_info[menu_name].get('action_name_list',[])
            action_connect_list = [self.updateToolbarNameList] * len(action_name_list)
            self.__addAction(menu=toolMenu,
                             action_name_list=action_name_list,
                             action_connect_list=action_connect_list,
                             action_dict=self.toolbar_action_dict,
                             checkable=True,
                             action_store=True)
            toolMenu.addSeparator()

        ##help menu
        helpMenu = menubar.addMenu('Help')
        action_name_list = ['Manual', 'Api Document', 'Install && Update', 'About']
        action_connect_list = [self.introduction,
                               self.apiDocument, 
                               self.install_update, 
                               self.about]
        self.__addAction(menu=helpMenu,
                         action_name_list=action_name_list,
                         action_connect_list=action_connect_list)

    def updateToolbarNameList(self):
        self.toolbar_name_list = [None]
        for action_name, action in self.toolbar_action_dict.items():
            if action.isChecked():
                self.toolbar_name_list.append(action_name)
        self.__createToolBar(update=True)

    def updateToolbarMenuStatus(self):
        for action_name, action in self.toolbar_action_dict.items():
            if action_name in self.toolbar_name_list:
                action.setChecked(True)
            else:
                action.setChecked(False)

    def setDefaultToolbar(self):
        self.toolbar_name_list = copy.deepcopy(self.toolbar_default_name_list)
        self.__createToolBar(update=True)

    def __addAction(self, menu, action_name_list, action_connect_list,
                    action_dict=None,icon_list=None,short_cut_list=None,
                    separetor_list=None,action_store=False,checkable=False,action_name_filter=None):
        if action_dict is None:
            action_dict = self.action_dict
        if action_name_filter is None:
            action_name_filter = []
        self.caseWindow.addAction(menu=menu,
                                  action_dict=action_dict,
                                  action_name_list=action_name_list,
                                  action_connect_list=action_connect_list,
                                  icon_list=icon_list,
                                  short_cut_list=short_cut_list,
                                  separetor_list=separetor_list,
                                  action_store=action_store,
                                  checkable=checkable,
                                  action_name_filter=action_name_filter,
                                  parent=self)
        return action_dict

    def about(self):
        html_file = os.path.join(os.getcwd(), 'ui/help/html/about.htm')
        help.openHtml(html_file)

    def apiDocument(self):
        html_file = os.path.join(os.getcwd(), 'ui/help/html/api_document.htm')
        help.openHtml(html_file)

    def introduction(self):
        html_file = os.path.join(os.getcwd(), 'ui/help/html/introduction.htm')
        help.openHtml(html_file)

    def install_update(self):
        html_file = os.path.join(os.getcwd(), 'ui/help/html/install_update.htm')
        help.openHtml(html_file)

    def __newCase(self):
        self.caseWindow.newCase()
      
    def __createToolBar(self, update=False):
        if not update:
            self.toolbar = self.addToolBar('Toolbar')
        else:
            self.toolbar.clear()
        icon_list = []
        action_name_list = []
        action_connect_list = []
        short_cut_list = []
        separetor_list = []
        for menu_name in ['file', 'edit']:
            icon_list += self.toolbar_info.get(menu_name, {}).get('icon_list',[])
            action_name_list += self.toolbar_info.get(menu_name, {}).get('action_name_list',[])
            action_connect_list += self.toolbar_info.get(menu_name, {}).get('action_connect_list',[])
            short_cut_list += self.toolbar_info.get(menu_name, {}).get('short_cut_list',[])
            separetor_list += self.toolbar_info.get(menu_name, {}).get('separetor_list',[])
        self.__addAction(menu=self.toolbar,
                         action_name_list=action_name_list,
                         action_connect_list=action_connect_list,
                         icon_list=icon_list,
                         short_cut_list=short_cut_list,
                         separetor_list=separetor_list,
                         action_store=True,
                         action_name_filter=self.toolbar_name_list)
  
        #add another toolbar: device toolbar
        if not update:
            self.device_toolbar = PyQt5.QtWidgets.QToolBar('Device')
        else:
            self.device_toolbar.clear()
        space = PyQt5.QtWidgets.QWidget(self)
        space.setSizePolicy(PyQt5.QtWidgets.QSizePolicy.Expanding, 
                            PyQt5.QtWidgets.QSizePolicy.Expanding)
        self.device_toolbar.addWidget(space)
        icon_list = self.toolbar_info.get('tools', {}).get('icon_list',[])
        action_name_list = self.toolbar_info.get('tools', {}).get('action_name_list',[])
        action_connect_list = self.toolbar_info.get('tools', {}).get('action_connect_list',[])
        short_cut_list = self.toolbar_info.get('tools', {}).get('short_cut_list',[])
        self.__addAction(menu=self.device_toolbar,
                         action_name_list=action_name_list,
                         action_connect_list=action_connect_list,
                         icon_list=icon_list,
                         short_cut_list=short_cut_list,
                         action_store=True,
                         action_name_filter=self.toolbar_name_list)
        self.addToolBar(PyQt5.QtCore.Qt.ToolBarArea(PyQt5.QtCore.Qt.TopToolBarArea), 
                        self.device_toolbar)
#        self.action_dict['Stop'].setEnabled(False)
        self.updateDeviceToolbar(['Find Widget'], [False])
        self.updateToolbarMenuStatus()

    def setDeviceConnectMenu(self):
        deviceMenu = PyQt5.QtWidgets.QMenu()
        action_name_list = ['iAuto', 'Windows', 'IOS', 'Android']
        action_connect_list = [self.connect_iAuto, self.connectWindows,
                               self.connectIOS, self.connectAndroid]
        icon_list = ['navigator.png', 'windows.png', 'ios.png', 'android.png']
        self.__addAction(menu=deviceMenu,
                         action_name_list=action_name_list,
                         action_connect_list=action_connect_list,
                         icon_list=icon_list
                         )
        device_action = self.action_dict.get('Device Connect')
        device_action.setMenu(deviceMenu)
        device_action.setIconVisibleInMenu(True)

    def showDeviceConnectMenu(self):
        if self.deviceList.isVisible():
            self.deviceList.hide()
        else:
            if self.connect_flag:
                self.deviceList.show()
            else:
                device_action = self.action_dict.get('Device Connect')
                device_connect_btn = self.device_toolbar.widgetForAction(device_action)
                x, y = device_connect_btn.x(), device_connect_btn.y()
                y += device_connect_btn.height()
                device_action.menu().exec_(self.device_toolbar.mapToGlobal(PyQt5.QtCore.QPoint(x,y)))

    def showDeviceConnect(self):
        if self.deviceList.isVisible():
            self.deviceList.hide()
        else:
            self.deviceList.show()
            self.deviceList.clearRedundantConnectWidget()

    def connect_iAuto(self):
        '''
            connect navigator real machine: iAuto
        '''
        import ui.device.setting
        uri = ui.device.setting.DEVICE_URI
        #uri = 'iauto:///?ip=127.0.0.1&port=5391'
        self.deviceList.device_platform = 'iauto'
        self.showDeviceConnect(uri)

    def connectWindows(self):
        '''
            connect windows program
        '''
        uri = "Windows:///?title_re=.*your windows program title.*"
        self.showDeviceConnect(uri,'windows')

    def connectIOS(self):
        #return
        '''
            connect IOS device
        '''
        uri = 'ios:///'
        self.showDeviceConnect(uri, 'ios')

    def connectAndroid(self):
        #return
        '''
            connect Android device
        '''
        uri = 'Android:///'
        self.showDeviceConnect(platform='android')

    def showAssistanter(self):
        self.assistanter.showAssistanter()
        if self.assistanter.isVisible() and deviceController.REC.DEVICE_NUM > 1:
            self.writeDeviceUriParas()

    def deviceController(self):
        self.device_controller = deviceController.CDeviceController(self)
        w = self.device_controller.width()
        p = self.mapToGlobal(PyQt5.QtCore.QPoint(self.width()-1, 0))
        x, y = p.x(), p.y()
        self.device_controller.move(PyQt5.QtCore.QPoint(x - w -200, y))
        self.device_controller.show()

    def writeDeviceUriParas(self):
#         reply = PyQt5.QtWidgets.QMessageBox.question(self, 'Device Uri Write',
#                                                     'Are you need to write device uri parameters ?',
#                                                     PyQt5.QtWidgets.QMessageBox.Yes,
#                                                     PyQt5.QtWidgets.QMessageBox.No)
#         if reply == PyQt5.QtWidgets.QMessageBox.Yes:
        if True:
            for index , uri in enumerate(self.getDeviceList()):
                dev_name = 'DEV%s' % (index+1)
                deviceController.REC.DEVICE_URI_MAPPING[uri] = dev_name
                para = "%s = '%s'" % (dev_name, uri)  + os.linesep
                self.assistanter.insertText(para)
            self.assistanter.insertText(os.linesep)
        else:
            return

    def setRecMode(self):
        self.rec_flag = not self.rec_flag
        deviceController.REC.FLAG = self.rec_flag
        deviceController.REC.ASST = self.assistanter
        if self.rec_flag:
            self.action_dict['Record Mode'].setIcon(PyQt5.QtGui.QIcon(':/icon/rec2.png'))
            self.action_dict['Record Mode'].setToolTip('Recording...')
            if deviceController.REC.DEVICE_NUM > 1:
                self.writeDeviceUriParas()
        else:
            self.action_dict['Record Mode'].setIcon(PyQt5.QtGui.QIcon(':/icon/rec.png'))
            self.action_dict['Record Mode'].setToolTip('Record Mode')
            self.device.hideWidget()

    def findWidget(self):
        self.device.device_proxy.pause()
        self.device.screen.widget_flag = True
        self.action_dict['Find Widget'].setEnabled(False)
        self.device.screen.widget_find_flag = True
#        self.device.device_proxy.resume()

    def findTree(self):
        self.device.device_proxy.pause()
#        self.widgetTree.hideSearch()
        self.widgetTree.showSearch()
#        try:
#            finder = treeFinder.CTreeFinder(self.widgetTree)
#            finder.exec_()
#        except:
#            import traceback
#            print(traceback.print_exc())

    def __exit(self):
        self.saveHistory()
        PyQt5.QtWidgets.qApp.quit()

    def stop(self):
        import threading
        t = threading.Thread(target=self.stopRun)
        t.start()

    def stopRun(self):
        try:
            self.case_run_proc[0].kill()
            print('Abort forced by user...')
        except:
            pass
        self.case_run_proc[0] = 0
        proc_len = len(self.case_run_proc) - 1
        i = proc_len
        if i > 0:
            while i < len(self.case_run_proc):
                try:
                    self.case_run_proc[i].kill()
                    print('Abort forced by user...')
                except:
                    pass
                time.sleep(1)
                i += 1
        self.case_run_proc = []

    def caseManagerRun(self):
        case_dir = self.caseWindow.getCurrentPath().replace('/', os.sep)
        self.run(case_dir)

    def caseManagerMultiRun(self):
        flag = False
        filepath = self.caseWindow.getCurrentPath().replace('/', os.sep)
        if os.path.isdir(filepath):
            if filepath.endswith('.air'):
                flag = True
            else:
                for f in os.listdir(filepath):
                    if f.endswith('.air') and os.path.isdir(os.path.join(filepath, f)):
                        flag = True
                        break
        if not flag:
            self.caseWindow.message('Run Configurations','No valid multi run directory !')
            return
        self.shell.clear()
        import autost.api
        from autost.case import manager
        parameters = multiRunConfig.CConfig(case=filepath, device=self.getDeviceUriList())
        parameters.init()
        parameters.exec_()
        rounds = parameters.paras.get('rounds', 0)
        logdir = parameters.paras.get('logdir', '')
        case = parameters.paras.get('case', '')
        device = parameters.paras.get('device')
        if case.endswith('.air'):
            if logdir == os.path.join(case, 'log'):
                logdir = ''
        else:        
            if logdir == case:
                logdir = ''
        func = manager.handle
        func_args = (filepath,
                     device,
                     logdir,
                     rounds)
        if rounds:
            try:
                import threading
                t = threading.Thread(target=self.runCase, args=(func, func_args))
                t.start()
            except:
                import traceback
                print(traceback.print_exc())

    def __runOne(self):
        self.__saveFile()
        index = self.editor.currentIndex()
        filename = self.editor.tabToolTip(index)
        filename = os.path.abspath(filename)
        self.run(filename)

    def getDeviceList(self):
        device_uri_list = []
        for uri_edit in self.deviceList.uri_edit_list:
            if uri_edit and uri_edit.currentText():
                device_uri_list.append(uri_edit.currentText())
        return device_uri_list

    def getDeviceUriList(self):
        device_uri_list = self.getDeviceList()
        if len(device_uri_list) == 0:
            device_uri_list = ''
        else:
            device_uri_list = '||'.join(device_uri_list)
        return device_uri_list

    def run(self, case_dir):
#        import autost.api
#        device=autost.api.G.DEVICE_URI
        device = self.getDeviceUriList()
        multi_flag = False
        if case_dir.endswith('.air') and os.path.isdir(case_dir):
            casename = case_dir[case_dir.rfind(os.path.sep)+1:-4]
            case = None
            for f in os.listdir(case_dir):
                if f == casename + '.py':
                    case = os.path.join(case_dir, f)
                    break
        elif case_dir.endswith('.py') and os.path.isfile(case_dir):
            file_list = case_dir.split(os.sep)
            if file_list[-1][:-3] == file_list[-2][:-4]:
                case_dir = os.sep.join(file_list[:-1])
                casename = file_list[-1][:-3]
                case = case_dir
            else:
                case = None
        else:
            case = None
            if os.path.isdir(case_dir):
                for f in os.listdir(case_dir):
                    if f.endswith('.air') and os.path.isdir(os.path.join(case_dir, f)):
                        multi_flag = True
                        case = case_dir
                        break   
        if not case:
            self.caseWindow.message('Run','No valid .air case exists !')
            return
        self.caseWindow.newFileRefresh(case_dir, False)
        self.shell.clear()
        import threading
        import autost.case.executor
        from autost.case import manager
        time_mark = time.strftime('%Y%m%d_%H%M%S',time.localtime(time.time()))
        if not multi_flag:
            logdir = os.path.sep.join([case_dir, 'log',
                                       '%s.log.%s' % (casename,time_mark)]
                                      )
            func = autost.case.executor.execute
            fifth_arg = True
        else:
            func = manager.handle
            fifth_arg = 1
            logdir = ''
        func_args = (case,
                     device,
                     logdir,
                     fifth_arg)
        t = threading.Thread(target=self.runCase, args=(func, func_args))
        t.start()

    def runCase(self, func, args):
#        self.action_dict['Stop'].setEnabled(True)
        self.shell.action.setEnabled(True)
        sys.stdout = EmittingStream(textWritten=self.simpleOutput)
        sys.stderr = EmittingStream(textWritten=self.simpleOutput)
        print(args)
        case, device, logdir, arg = args
        func(case, device, logdir, arg, self.case_run_proc)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        #time.sleep(3.0)
        #self.device.device_proxy.resume()
#        self.action_dict['Stop'].setEnabled(False)
        self.shell.action.setEnabled(False)

    def __newFile(self):
        self.caseWindow.newFile()

    def __saveFile(self):
        try:
            index = self.editor.currentIndex()
            filename = self.editor.tabToolTip(index)
            try:
                file_content = self.editor.currentWidget().scintilla.text()
            except:
                file_content = self.editor.currentWidget().toHtml()
                file_content = self.html2text(file_content,
                                              self.editor.template_paras.get(filename, {}))
            file_content = file_content.replace('\r\n', '\n')
            with open(filename, 'w') as f:
                f.write(file_content)
            self.editor.currentWidget().change_times = 0
            self.statusBar.showMessage('save file : %s' % filename)
            self.updateToolbar()
        except:
            import traceback
            print(traceback.print_exc())
        
    def __saveFileAs(self):
        filename, _ = PyQt5.QtWidgets.QFileDialog.getSaveFileName(self, 'New File',
                                                                  os.getenv('HOME'),
                "All Files(*);;Python Files(*.py);;Text Files (*.txt);;Image(*.png)")
        try:
            file_content = self.editor.currentWidget().scintilla.text()
        except:
            file_content = self.editor.currentWidget().toHtml()
            file_content = self.html2text(file_content)
        file_content = file_content.replace('\r\n', '\n')
        if filename:
            with open(filename, 'w') as f:
                f.write(file_content)
            self.openFile(filename)

    def __saveAllFile(self):
        tip_index_dict = self.editor.getToolTipIndex()
        for filename, i in tip_index_dict.items():
            change_times = self.editor.widget(i).change_times
            if change_times < 1:
                continue
            try:
                file_content = self.editor.widget(i).scintilla.text()
            except:
                file_content = self.editor.widget(i).toHtml()
                file_content = self.html2text(file_content,
                                              self.editor.template_paras.get(filename, {}))
            file_content = file_content.replace('\r\n', '\n')
            with open(filename, 'w') as f:
                f.write(file_content)
            self.editor.widget(i).change_times = 0
        for action_name in ['Save', 'Save All']:
            self.action_dict[action_name].setEnabled(False)

    def __setting(self):
        setting_dialog = setting.CSetting(self)
        setting_dialog.exec_()

    def openFile(self, filename=None, editor_type=True):
        try:
            if not filename:
                filename, _ = PyQt5.QtWidgets.QFileDialog.getOpenFileName(self, 'Open File',
    																	  'workspace',
    					"All Files(*);;Python Files(*.py);;Text Files (*.txt);;Image(*.png)")
            tip_index_dict = self.editor.getToolTipIndex()
            if filename in tip_index_dict.keys():
                index = tip_index_dict[filename]
                self.editor.setCurrentIndex(index)
                return
            fh = None
            if PyQt5.QtCore.QFile.exists(filename):
                fh = PyQt5.QtCore.QFile(filename)
            if not fh:
                return
            fh.open(PyQt5.QtCore.QFile.ReadWrite)
            data = fh.readAll()
            codec = PyQt5.QtCore.QTextCodec.codecForUtfText(data) 
            unistr = codec.toUnicode(data)
            self.editor.addTable(unistr, filename, editor_type)
            self.updateToolbar()
        except:
            import traceback
            print(traceback.print_exc())
         
    def closeEvent(self, event):
        reply = PyQt5.QtWidgets.QMessageBox.question(self, 'Message',
                                           "Are you sure to quit?",
                                           PyQt5.QtWidgets.QMessageBox.Yes,
                                           PyQt5.QtWidgets.QMessageBox.No)
        if reply == PyQt5.QtWidgets.QMessageBox.Yes:
            if self.action_dict['Save All'].isEnabled():
                reply2 = PyQt5.QtWidgets.QMessageBox.question(self, 'Message',
                                               "Some files has been modified. Save changes?",
                                               PyQt5.QtWidgets.QMessageBox.Yes|PyQt5.QtWidgets.QMessageBox.No|PyQt5.QtWidgets.QMessageBox.Cancel)
                if reply2 == PyQt5.QtWidgets.QMessageBox.Yes:
                    self.__saveAllFile()
                elif reply2 == PyQt5.QtWidgets.QMessageBox.Cancel:
                    event.ignore()
                    return
                else:
                    pass
            self.saveHistory()
            event.accept()
        else:
            event.ignore()

    @trace
    def saveHistory(self):
        history = {}
        current_index = self.editor.currentIndex()
        items = self.editor.getToolTipIndex().items()
        items = sorted(items, key=lambda e:int(e[1]))
        history_file_list = []
        editor_type_list = []
        for filename, index in items:
            history_file_list.append(filename)
            editor_type_list.append(self.editor.editor_type_dict[filename])
        history_file_list = [os.path.relpath(f, os.getcwd()) for f in history_file_list]
        history_file_list = [f.replace(os.sep, '/') for f in history_file_list]
        history['editor_type'] = editor_type_list
        history['file_list'] = history_file_list
        history['current_index'] = current_index
        expanded_nodes = self.caseWindow.findExpandedNode()
        history['expanded_nodes'] = expanded_nodes
        history = json.dumps(history,sort_keys=True,
                             indent = 6,skipkeys=True,ensure_ascii = False)
        if not os.path.isdir('ui/history'):
            os.makedirs('ui/history')
        with open('ui/history/history.json', 'w') as f:
            f.write(history)

    def loadHistory(self):
        try:
            history = json.load(open('ui/history/history.json'))
        except:
            history = {}
        history_file_list = history.get('file_list', [])
        history_file_list = [caseAttributesSetting.CAttributesSetting.getAbsPath(f, os.getcwd())
                             for f in history_file_list]
        history_file_list = [f.replace(os.sep, '/') for f in history_file_list]
        editor_type_list = history.get('editor_type', [])
        try:
            for i in range(len(history_file_list)):
                self.openFile(history_file_list[i], editor_type_list[i])
        except:
            pass
        index = history.get('current_index', -1)
        if index > -1:
            self.editor.setCurrentIndex(index)
        expanded_nodes = history.get('expanded_nodes', [])
        self.caseWindow.expandedNodes(expanded_nodes)

    def autoCoding(self, filename):
        name = filename.replace(os.sep, '/').split('/')[-1]
        self.statusBar.showMessage('auto coding...')
        try:
            editor = self.editor.currentWidget()
            if editor:
                try:
                    editor.scintilla.insert(TEMPLATE % name)
                    x, y = editor.scintilla.getCursorPosition()
                    editor.scintilla.setCursorPosition(x+1, y)
                    editor.scintilla.setFocus()
                except:
                    editor.insertImage(filename)
                    editor.setFocus()
        except:
            import traceback
            print(traceback.print_exc())

    def updateDeviceToolbar(self, name_list, flag_list):
        for i in range(len(name_list)):
            try:
                self.action_dict[name_list[i]].setEnabled(flag_list[i])
            except:
                pass

    def updateToolbar(self):
        try:
            self.action_dict['Screen Capture'].setEnabled(not self.captureWindow.screen.capture_flag)
        except:
            pass
        tab_count = self.editor.count()
        if tab_count < 1:
            for action_name in ['Save', 'Save All', 'Run', 'Save As','Change Editor']:
                self.action_dict[action_name].setEnabled(False)
        else:
            for action_name in ['Run', 'Save As', 'Change Editor']:
                self.action_dict[action_name].setEnabled(True)
            if self.editor.currentWidget().change_times > 0:
                self.action_dict['Save'].setEnabled(True)
                self.action_dict['Save All'].setEnabled(True)
            else:
                self.action_dict['Save'].setEnabled(False)    
                save_all_flag = False
                for i in range(tab_count):
                    try:
                        if self.editor.widget(i).change_times > 0:
                            save_all_flag = True
                            break
                    except:
                        pass
                self.action_dict['Save All'].setEnabled(save_all_flag)

    def updateCtrlAltFlag(self):
        self.editor.ctrl_alt_flag = self.ctrl_alt_flag
        self.current_device.screen.ctrl_alt_flag = self.ctrl_alt_flag
        if self.ctrl_alt_flag == 1:
            if hasattr(self.current_device, 'device_proxy'):
                self.current_device.device_proxy.resume()
            if self.current_device.screen.getWidgetTreeDataFlag():
                self.statusBar.showMessage('Alt pressed: device [ touch(v) ] change to [ touch(point) ]')
            else:
                self.statusBar.showMessage('Alt pressed: capture and then touch')
        elif self.ctrl_alt_flag == 2:
            if self.rec_flag:
                if hasattr(self.current_device, 'device_proxy'):
                    self.current_device.device_proxy.pause()
            self.statusBar.showMessage('Ctrl pressed: device [ touch ] change to [ assert_exists ]')
        elif self.ctrl_alt_flag == 3:
            if self.rec_flag:
                if hasattr(self.current_device, 'device_proxy'):
                    self.current_device.device_proxy.pause()
            self.current_device.hideWidget()
            self.current_device.screen.repaint()
            self.statusBar.showMessage('Ctrl+Alt pressed!')
        else:
            if hasattr(self.current_device, 'device_proxy'):
                self.current_device.device_proxy.resume()

    def keyReleaseEvent(self, event):
        if event.key() == PyQt5.QtCore.Qt.Key_Control:
            self.statusBar.showMessage('Ctrl released !')
            self.ctrl_alt_flag &= 1
            self.updateCtrlAltFlag()
        if event.key() == PyQt5.QtCore.Qt.Key_Alt:
            self.statusBar.showMessage('Alt released !')
            self.ctrl_alt_flag &= 2
            self.updateCtrlAltFlag()

    def keyPressEvent(self, event):
        if event.modifiers() == PyQt5.QtCore.Qt.ControlModifier | PyQt5.QtCore.Qt.AltModifier:
            self.ctrl_alt_flag = 3
            self.updateCtrlAltFlag()
        if event.modifiers() == PyQt5.QtCore.Qt.ControlModifier:
            self.ctrl_alt_flag |= 2
            self.updateCtrlAltFlag()
        if event.modifiers() == PyQt5.QtCore.Qt.AltModifier:
            self.ctrl_alt_flag |= 1
            self.updateCtrlAltFlag()
        if event.key() == PyQt5.QtCore.Qt.Key_Escape:
            self.current_device.hideWidget()
        elif event.key() == PyQt5.QtCore.Qt.Key_Delete:
            self.caseWindow.delete()
        elif PyQt5.QtCore.Qt.ControlModifier and event.key() == PyQt5.QtCore.Qt.Key_C:
            self.caseWindow.copy()
        elif PyQt5.QtCore.Qt.ControlModifier and event.key() == PyQt5.QtCore.Qt.Key_V:
            self.caseWindow.paste()
        elif PyQt5.QtCore.Qt.ControlModifier and event.key() == PyQt5.QtCore.Qt.Key_F:
            self.findTree()
        elif event.key() == PyQt5.QtCore.Qt.Key_F5:
            self.caseWindow.rootRefresh()
        elif event.key() == PyQt5.QtCore.Qt.Key_F2:
            self.caseWindow.rename()
        else:
            PyQt5.QtWidgets.QWidget.keyPressEvent(self, event)

    def mousePressEvent (self, event):
        try:
            self.device_controller.close()
        except:
            pass

    def mapToScreen(self, point):
        pixmap = self.current_device.pixmap
        pixmap_size = (pixmap.width(), pixmap.height())
        ide_point = PyQt5.QtCore.QPoint(point[0], point[1])
        global_point = self.mapToGlobal(ide_point)
        screen_point = self.current_device.screen.mapFromGlobal(global_point)
        x, y = screen_point.x(), screen_point.y()
        scale = self.current_device.getScale()
        x, y = list(map(lambda x: int(x / scale), [x, y]))
        if x >=0 and x < pixmap_size[0] and y >=0 and y < pixmap_size[1]:
            return [x, y]
        else:
            return None

    def html2text(self, data, template_paras):
        return htmlParser.html2text(data, template_paras)

    @trace
    def changeEditor(self):
        file_dict = {v:k for k, v in self.editor.getToolTipIndex().items()}
        if len(file_dict) == 0:
            return
        index = self.editor.currentIndex()
        if index == -1:
            return
        change_times = self.editor.widget(index).change_times
        filename = file_dict[index]
        tabname = self.editor.tabText(index)
        editor_type = self.editor.editor_type_dict.get(filename)
        if editor_type: 
            file_content = self.editor.widget(index).scintilla.text()
            scrollbar = self.editor.currentWidget().scintilla.verticalScrollBar()
        else:
            file_content = self.editor.widget(index).toHtml()
            file_content = self.html2text(file_content, 
                                          self.editor.template_paras.get(filename, {}))
            scrollbar = self.editor.currentWidget().verticalScrollBar()
        scrollbar_value_org = scrollbar.value()
        scrollbar_max_org = scrollbar.maximum()
        self.editor.removeTable(index)
        editor_type = not editor_type
        self.editor.editor_type_dict[filename] = editor_type
        if editor_type:
            self.statusBar.showMessage('Editor Type : Plain Text')
        else:
            self.statusBar.showMessage('Editor Type : Rich Text')
        self.editor.insertTable(index, file_content, filename, tabname, editor_type)
        self.editor.setCurrentIndex(index)
        self.editor.currentWidget().change_times = change_times
        try:
            scrollbar_max_dest = self.editor.currentWidget().verticalScrollBar().maximum()
        except:
            scrollbar_max_dest = self.editor.currentWidget().scintilla.verticalScrollBar().maximum()
        if scrollbar_max_org and scrollbar_max_dest:
            scrollbar_value_dest = round(scrollbar_value_org * 1.0 / scrollbar_max_org * scrollbar_max_dest)
        else:
            scrollbar_value_dest = 0
        try:
            self.editor.currentWidget().verticalScrollBar().setValue(0)
            self.editor.currentWidget().lineNumberArea.repaint()
            self.editor.currentWidget().verticalScrollBar().setValue(scrollbar_value_dest)
        except:
            self.editor.currentWidget().scintilla.verticalScrollBar().setValue(scrollbar_value_dest)
        self.updateToolbar()

    def updateWidgetTreeOrgRect(self, org_rect):
        self.widgetTree.org_rect = org_rect

    def updateDeviceWidgetRect(self):
        zoom_factor = self.current_device.getScale()
#        self.current_device.screen.widget_org_rect = self.widgetTree.org_rect
        self.current_device.screen.widget_rect = list(map(lambda k : int(k * zoom_factor),
                                                  self.widgetTree.org_rect))

    def showWidget(self, x, y):
        item, rect, org_rect = self.widgetTree.findWidgetFromPoint((x, y))
        if item:
            self.widgetTree.org_rect = org_rect
            self.updateDeviceWidgetRect()
            self.current_device.screen.repaint()
            current_item = self.widgetTree.tree.currentItem()
            try:
                self.widgetTree.tree.expandItem(item)
                self.widgetTree.tree.setCurrentItem(item)
            except:
                pass
            self.showWidgetProperties(item)

    @trace
    def InsertAsCapture(self):
        index = self.caseWindow.tree.currentIndex()
        filepath = self.caseWindow.model.filePath(index).replace('/', os.sep)
        if filepath.split(os.sep)[-1].split('.')[-1] not in ['jpg', 'png']:
            self.caseWindow.message('Insert As Capture', 'Not a Picture !')
            return
        file_dict = {v:k for k, v in self.editor.getToolTipIndex().items()}
        filename = file_dict[self.editor.currentIndex()]
        paste_dir = os.sep.join(filename.split('/')[:-1])
        if os.sep.join(filepath.split(os.sep)[:-1]) == paste_dir:
            paste_file = filepath
        else:
            self.caseWindow.copy_file_list = [filepath]
            paste_file = self.caseWindow.paste(paste_dir)[0]
        self.autoCoding(paste_file)

    @trace
    def caseManagerDataChange(self, index1, index2, role_list):
        org_filepath = self.caseWindow.rename_filepath
        new_filepath = self.caseWindow.model.filePath(index1)
        editor_tip_dict = self.editor.getToolTipIndex()
        tab_index = editor_tip_dict.get(org_filepath)
        if tab_index:
            tab_name = self.editor.getTabName(new_filepath)
            self.editor.setTabText(tab_index, tab_name)
            self.editor.setTabToolTip(tab_index, new_filepath)
        self.caseWindow.rename_filepath = None

    @trace
    def caseManagerDelete(self):
        if not self.caseWindow.question('Are you sure you want to delete ?'):
            return
        self.caseWindow.model.setResolveSymlinks(False)
        filepath_list = self.caseWindow.getSelectedPath()
        self.caseWindow.model.setResolveSymlinks(True)
        for filepath in filepath_list:
            file_list = []
            if os.path.isfile(filepath):
                file_list.append(filepath)
            else:
                for root, dir, files in os.walk(filepath):
                    for f in files:
                        file_list.append(os.path.join(root, f))
            editor_tip_dict = self.editor.getToolTipIndex()
            for f in file_list:
                editor_index = editor_tip_dict.get(f.replace(os.sep, '/'), -1)
                if editor_index > -1:
                    self.editor.removeTable(editor_index)
            if os.path.islink(filepath):
                os.unlink(filepath)
            else:
                if os.path.isdir(filepath):
                    shutil.rmtree(filepath)
                else:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
            self.statusBar.showMessage('delete file: %s' % filepath)
        parent_list = []
        for f in filepath_list:
            parent = os.sep.join(f.split(os.sep)[:-1])
            if parent not in parent_list + filepath_list:
                parent_list.append(parent)
                index = self.caseWindow.model.index(parent)
                self.caseWindow.refresh(index)

    def setScreenSize(self):
        self.widgetTree.screen_size = (self.current_device.pixmap.width(),
                                             self.current_device.pixmap.height())

    @trace
    def showWidgetProperties(self, item=None):
        if not item:
            item = self.widgetTree.tree.currentItem()
            property = self.widgetTree.properties.get(str(item), [{},None])[0]
        self.widgetInfo.editor.clear()
        #for k, v in property.items():
        for k in sorted(property.keys()):
            if k in ('pos', 'size'):
                continue
            v = property[k]
            if k in ('className', ):
                v = v.replace('N11QQmlPrivate11QQmlElementI', '')
#                m = re.search('[a-zA-Z]+$', v)
#                if m:
#                    v = '%s.%s' % (v, m.group(0))
            t = '\t' * (2 - int((len(k) + 2) / 7))
            self.widgetInfo.editor.insertPlainText('%s: %s%s\n' % (k, t, v))

    def setZoomFactor(self):
        self.widgetTree.zoom_factor = self.current_device.getScale()

    @trace
    def showWidgetFromItem(self, item):
        self.current_device.device_proxy.pause()
        self.current_device.screen.widget_flag = True
        self.action_dict['Find Widget'].setEnabled(False)
        if not item:
            item = self.widgetTree.tree.currentItem()
        else:
            self.widgetTree.tree.setCurrentItem(item)
        self.widgetTree.tree.expandItem(item)
        try:
            property = self.widgetTree.properties.get(str(item))[0]
        except:
            property = {}
        self.current_device.updateScreen()
        rect, self.widgetTree.org_rect = self.widgetTree.getRect(property)
        self.current_device.screen.setRect(rect)
        self.current_device.screen.repaint()

    def screenCapture(self, auto_naming=False):
        self.captureWindow.screen.capture_flag = True
        self.captureWindow.setDevice(self.current_device)
        self.updateToolbar()
        self.captureWindow.screen.case_dir = self.getCaseDir()
        self.captureWindow.capture(auto_naming)

    def getCaseDir(self):
        index = self.editor.currentIndex()
        if index > -1:
            filename = self.editor.tabToolTip(index)
            case_dir = '/'.join(filename.split('/')[:-1])
        else:
            case_dir = 'workspace'
        case_dir += '/Unnamed'
        return case_dir

    def setConnectFlag(self, flag):
        self.connect_flag = flag

    def voiceSetting(self):
        self.vrSetting = vrSetting.VR_Controller(self)
        w = self.vrSetting.width()
        p = self.mapToGlobal(PyQt5.QtCore.QPoint(self.width() - 1, 0))
        x, y = p.x(), p.y()
        self.vrSetting.move(PyQt5.QtCore.QPoint(x - w - 200, y))
        self.vrSetting.exec_()

    def connect_vr_server(self, ip):
        ip_config = ip.split(":")
        if len(ip_config) != 2:
            print("input error ...")
            return False
        return self.vr_client.connect(ip_config[0], ip_config[1])

    def disconnect_vr_server(self):
        self.vr_client.stop()
        self.vr_client.disconnect()

    def send_data_to_server(self, data):
        self.vr_client.send(data)

    def set_connect_status(self, status):
        self.connect_status = status

    def get_connect_status(self):
        return self.connect_status


class CIDE:
    def run(self):
        try:
            import cgitb
            cgitb.enable(format = 'text')
            app = PyQt5.QtWidgets.QApplication(sys.argv)
            w = CIDEWindow()
            w.showMaximized()
#            w.device.connect_device()
#            w.device.device_proxy.widgetTreeUpdate.connect(w.widgetTree.updateTree)
#            w.connect_iAuto()
            w.deviceList.connect_init()
            sys.exit(app.exec_())
        except SystemExit:
            pass
        except:
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    CIDE().run()
        

