# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-7-24

@author: wushengbing
'''
import sys
import os
import shutil
import json
import PyQt5.QtWidgets
import PyQt5.QtGui
import PyQt5.QtCore
try:
    from . import multiRunConfig, shortcut
except:
    import multiRunConfig, shortcut

WIDTH = 400
ROW_HEIGHT = 30


class CAttributesSetting(multiRunConfig.CConfig):
    setupRefresh = PyQt5.QtCore.pyqtSignal(str, object)

    def __init__(self, fileinfo_list=[], case=None, device="iauto:///"):
        super(CAttributesSetting, self).__init__(case, device)
        self.fileinfo_list = fileinfo_list
        self.case = case
        self.device = device
        self.setWindowTitle('Properties...')

    def init(self):
        self.initGui()
        self.createLayout()
        self.btn_ok.pressed.connect(self.updateSetupTeardown)
        self.btn_cancel.pressed.connect(self.cancel)
        if self.case:
            self.btn_add.pressed.connect(self.addSetupEdit)
            self.btn_teardown_add.pressed.connect(self.addTeardownEdit)
        self.loadSetupTeardownFiles()

    def initGui(self):
        self.widget_list = []
        width = 0
        for name, value in self.fileinfo_list:
            file_label = PyQt5.QtWidgets.QLabel(name)
            file = PyQt5.QtWidgets.QLabel(value)
            file.setTextInteractionFlags(PyQt5.QtCore.Qt.TextSelectableByMouse)
            self.widget_list.append([file_label, file])
            if width < len(name + value):
                width = len(name + value)
        self.width = max(width * 10, WIDTH)
        self.index = 0
        self.setup_list = []
        self.teardown_list = []
        self.btn_file_list = []
        self.btn_delete_list = []
        self.btn_up_list = []
        self.btn_down_list = []
        self.btn_teardown_file_list = []
        self.btn_teardown_delete_list = []
        self.btn_teardown_up_list = []
        self.btn_teardown_down_list = []
        self.btn_ok = PyQt5.QtWidgets.QPushButton('OK')
        self.btn_cancel = PyQt5.QtWidgets.QPushButton('Cancel')
        self.title_label = PyQt5.QtWidgets.QLabel('Case Information')
        self.title_font = PyQt5.QtGui.QFont()
        self.title_font.setPointSize(10)
        self.title_font.setBold(True)
        self.title_label.setFont(self.title_font)
        self.createTemplateBtn()
        if self.case:
            self.initSetupTeardownGui()
        self.updateSize()

    def createTemplateBtn(self):
        self.default = PyQt5.QtWidgets.QPushButton('Set Template')
        self.default.setFixedSize(100,25)
        self.default.setToolTip('Set these setups and teardowns as template...')
        self.default.pressed.connect(self.setTemplate)

    def setTemplate(self):
        template = {'setups':[], 'teardowns':[]}
        for config_type in ('setups', 'teardowns'):
            if config_type == 'setups':
                edit_list = self.setup_list
            else:
                edit_list = self.teardown_list
            for s in edit_list:
                if s and s.text():
                    if s.text() not in template[config_type]:
                        template[config_type].append(s.text())
        template_config = {}
        ref_dir = os.getcwd()
        for k, v in template.items():
            rel_v = [os.path.relpath(s, ref_dir).replace(os.sep,'/') for s in v]
            template_config[k] = rel_v
        template_config = json.dumps(template_config, sort_keys=True,
                                     indent = 6,skipkeys=True,ensure_ascii = False)
        with open('ui/caseManager/template.json', 'w') as f:
            f.write(template_config)

    def createLine(self):
        line = PyQt5.QtWidgets.QFrame(self)
        line.setFrameShape(PyQt5.QtWidgets.QFrame.HLine)
        line.setFrameShadow(PyQt5.QtWidgets.QFrame.Sunken)
        return line

    def initSetupTeardownGui(self):
        self.attributes_title = PyQt5.QtWidgets.QLabel('Attributes:')
        self.attributes_title.setFont(self.title_font)
        self.case = PyQt5.QtWidgets.QLabel(self.paras.get('case'))
        self.case.setTextInteractionFlags(PyQt5.QtCore.Qt.TextSelectableByMouse)
        self.case_label =  PyQt5.QtWidgets.QLabel('CaseDir:')
        self.device_label = PyQt5.QtWidgets.QLabel('Device :')
        self.device = PyQt5.QtWidgets.QLabel(self.paras.get('device'))
        self.device.setTextInteractionFlags(PyQt5.QtCore.Qt.TextSelectableByMouse)
        self.setups_label =  PyQt5.QtWidgets.QLabel('Setups :')
        self.teardowns_label = PyQt5.QtWidgets.QLabel('Teardowns :')
        width = max(30,
                    len(self.paras.get('device')), 
                    len(self.paras.get('case')), 
                    len(self.paras.get('setups','')),
                    len(self.paras.get('teardowns',''))) * 10 + 180
        if self.width < width:
            self.width = width
#        self.btn_dir = self.createBtn()
        self.btn_add = self.createBtn("+")
        self.btn_teardown_add = self.createBtn("+")

    def createLayout(self):
        self.layout = PyQt5.QtWidgets.QGridLayout()
        self.layout.addWidget(self.title_label, 0, 0, 2, 5)
        if not self.case:
            self.layout.addWidget(self.createLine(), 2, 0, 1, 5)
        index = 3
        for name, value in self.widget_list:
            self.layout.addWidget(name, index, 0, 2, 1)
            self.layout.addWidget(value, index, 1, 2, 4)
            index += 2
        if self.case:
            self.layout.addWidget(PyQt5.QtWidgets.QLabel(), index, 0, 2, 5)
            index += 2
            self.layout.addWidget(self.attributes_title, index, 0, 2, 5)
            self.layout.addWidget(self.createLine(), 2, 0, 1, 9)
            index += 2
            self.layout.addWidget(self.createLine(), index, 0, 1, 9)
            index += 1
            widget_list = [ [self.case_label, self.case],
                            [self.device_label, self.device],
                            [self.setups_label, self.btn_add],
                            [self.teardowns_label,self.btn_teardown_add]
                           ]
            for widgets in widget_list:
                self.layout.addWidget(widgets[0], index, 0, 2, 1)
                try:
                    self.layout.addWidget(widgets[1], index, 1, 2, 4)
                except:
                    pass
                try:
                    self.layout.addWidget(widgets[2], index, 5, 2, 1)
                except:
                    pass
                index += 2
        self.layout.addWidget(self.btn_ok, index, 3, 2, 1)
        self.layout.addWidget(self.btn_cancel, index, 4, 2, 1)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 2)
        self.layout.setColumnStretch(2, 2)
        self.setLayout(self.layout)
        self.btn_ok.setFocus()
        self.btn_ok.setDefault(True)

    def updateParas(self):
        if not self.case:
            return
        self.paras['setups'] = []
        self.paras['teardowns'] = []
        for setup_edit in self.setup_list:
            if setup_edit:
                setup_text = setup_edit.text()
                if setup_text and setup_text not in self.paras['setups']:
                    if os.path.exists(setup_text):
                        self.paras['setups'].append(setup_text)
        for teardown_edit in self.teardown_list:
            if teardown_edit:
                teardown_text = teardown_edit.text()
                if teardown_text and teardown_text not in self.paras['teardowns']:
                    if os.path.exists(teardown_text):
                        self.paras['teardowns'].append(teardown_text)

    def updateSetupTeardown(self):
        if self.case:
            self.updateParas()
            caseDir = self.paras['case'].replace('/', os.sep)
            for config_type in ('setups', 'teardowns'):
                setup_dir = os.path.join(caseDir, config_type)
                setup_file_list = self.paras.get(config_type, [])
                self.addSetupTeardownFiles(setup_dir, setup_file_list)
                self.setupRefresh.emit(setup_dir, False)   
            self.updateSetupConfigFile()
            self.setupRefresh.emit(caseDir, False)
        self.close()

    @classmethod
    def addSetupTeardownFiles(cls, setup_dir, setup_file_list):
        config_type = '.' + setup_dir.split(os.sep)[-1][:-1]
        setup_list = [os.sep.join(f.split(os.sep)[:-1]) for f in setup_file_list]
        setup_list = list(set(setup_list))
        if os.path.isdir(setup_dir):
            for f in os.listdir(setup_dir):
                f_path = os.path.join(setup_dir, f)
                if f_path.endswith('.lnk'):
                    try:
                        dest_path = shortcut.getShortcutDestination(f_path)
                    except:
                        dest_path = None
                    if dest_path in setup_list:
                        setup_list.remove(dest_path)
                    else:
                        os.remove(f_path)
                elif f_path not in setup_list:
                    if os.path.isdir(f_path):
                        shutil.rmtree(f_path)
                    else:
                        os.remove(f_path)
                else:
                    pass
        else:
            os.mkdir(setup_dir)
        for setup in setup_list:
            path_list = setup.split(os.sep)
            if not setup.endswith(config_type):
                continue
            if os.sep.join(path_list[:-1]) == setup_dir:
                continue
            cls.importSetupFile(setup, setup_dir)

    @classmethod
    def importSetupFile(cls, src_setup, setup_dir):
        setup_name = src_setup.split(os.sep)[-1]
        dest_setup = os.path.join(setup_dir, setup_name)
        while 1:
            if os.path.exists(dest_setup + '.lnk'):
                dest_setup = cls.getSetupSymlinkName(dest_setup)
            else:
                break
        shortcut.createShortcut(src_setup, dest_setup)

    @classmethod
    def importSetupFile2(cls, src_setup, setup_dir):
        setup_name = src_setup.split(os.sep)[-1]
        dest_setup = os.path.join(setup_dir, setup_name)
        while 1:
            if os.path.exists(dest_setup):
                dest_setup = cls.getSetupSymlinkName(dest_setup)
            else:
                break
        src_setup = os.path.relpath(src_setup, setup_dir)
        dest_setup = os.path.relpath(dest_setup)
        os.symlink(src_setup, dest_setup)

    def getSymlinkAbsPath(self, symlink_path):
        symlink = os.readlink(symlink_path)
        current_dir = os.getcwd()
        os.chdir(symlink_path[:symlink_path.rfind(os.sep)])
        filepath = os.path.abspath(symlink)
        os.chdir(current_dir)
        return filepath

    @staticmethod
    def getAbsPath(relpath, ref_path):
        current_dir = os.getcwd()
        os.chdir(ref_path)
        abspath = os.path.abspath(relpath)
        os.chdir(current_dir)
        return abspath

    @staticmethod
    def getSetupSymlinkName(setup):
        tail = '.' + setup.split('.')[-1]
        name_list = setup.split(os.sep)
        name = name_list[-1].split(tail)[0]
        name_head = name.split('(')[0]
        try:
            name_num = int(name.split('(')[1].split(')')[0])
        except:
            name_num = 0
        name_num += 1
        new_name = name + '(%s)%s' % (name_num, tail)
        return os.sep.join(name_list[:-1] + [new_name])

    def updateSetupConfigFile(self):
        case_dir = self.paras.get('case')
        rel_paras = {}
        for k, v in self.paras.items():
            if k in ('setups', 'teardowns'):
                rel_v = [os.path.relpath(s, case_dir).replace(os.sep,'/') for s in v]
            elif k in ('device', 'case'):
                continue
#                rel_v = v
            else:
                try:
                    rel_v = os.path.relpath(v, case_dir).replace(os.sep,'/')
                except:
                    rel_v = v
            rel_paras[k] = rel_v
        setup_list = rel_paras.get('setups', [])
        if os.path.isdir(case_dir):
            setup_config = json.dumps(rel_paras, sort_keys=True,
                                      indent = 6,skipkeys=True,ensure_ascii = False)
            with open(os.path.join(case_dir, 'config.ini'), 'w') as f:
                f.write(setup_config)

    def updateCaseDir(self):
        dirname = self.setDir()
        self.case.setText(dirname)

    def loadSetupTeardownFiles(self):
        case_dir = self.paras.get('case')
        try:
            configs = json.load(open(os.path.join(case_dir, 'config.ini')))
        except:
            configs = {}
        for config_type in ('setups', 'teardowns'):
            setup_files = configs.get(config_type, [])
            abs_setup_files = [self.getAbsPath(s, case_dir) for s in setup_files]
            for setup_file in abs_setup_files:
                if config_type == 'setups':
                    self.addSetupEdit(setup_file)
                else:
                    self.addTeardownEdit(setup_file)
            if case_dir:
                setups_dir = os.path.join(case_dir, config_type)
                if os.path.isdir(setups_dir):
                    tail = '.' + config_type[:-1]
                    org_setup_list = [os.path.join(setups_dir, s) for s in os.listdir(setups_dir) \
                                      if s.endswith(tail) and not os.path.islink(os.path.join(setups_dir, s))]
                    for org_setup_dir in org_setup_list:
                        for f in os.listdir(org_setup_dir):
                            if f.endswith('.py'):
                                org_setup = os.path.join(org_setup_dir, f)
                                if org_setup not in abs_setup_files:
                                    if config_type == 'setups':
                                        self.addSetupEdit(org_setup)
                                    else:
                                        self.addTeardownEdit(org_setup)
        self.updateParas()
        self.updateSetupConfigFile()

    def addTeardownEdit(self, teardown_file=''):
        try:
            self.btn_teardown_delete_list.append(self.createBtn("-", self.index))
            self.btn_teardown_file_list.append(self.createBtn(btn_number=self.index))
            self.btn_teardown_up_list.append(self.createBtn('↑', self.index))
            self.btn_teardown_down_list.append(self.createBtn('↓', self.index))
            self.index += 1
            num = self.getRowCount() - 3
            self.teardown_list.append(PyQt5.QtWidgets.QLineEdit(teardown_file))
            self.layout.addWidget(self.teardown_list[-1], 2*num, 1, 2, 4)
            self.layout.addWidget(self.btn_teardown_file_list[-1], 2*num, 5, 2, 1)
            self.layout.addWidget(self.btn_teardown_delete_list[-1], 2*num, 6, 2, 1)
            self.layout.addWidget(self.btn_teardown_up_list[-1], 2*num, 7, 2, 1)
            self.layout.addWidget(self.btn_teardown_down_list[-1], 2*num, 8, 2, 1)
            self.layout.addWidget(self.btn_teardown_add, 2+2*num, 1, 2, 1)
            self.layout.addWidget(self.default, 4+2*num, 6, 2, 4)
            num += 1
            self.layout.addWidget(self.btn_ok, 4 +2*num, 3, 2, 1)
            self.layout.addWidget(self.btn_cancel, 4 +2*num, 4, 2, 1)
            self.btn_teardown_file_list[-1].pressed.connect(self.updateTeardown)
            self.btn_teardown_delete_list[-1].pressed.connect(self.deleteTeardownEdit)
            self.btn_teardown_up_list[-1].pressed.connect(self.teardownEditUp)
            self.btn_teardown_down_list[-1].pressed.connect(self.teardownEditDown)
            self.updateTeardownEditDownState()
            self.updateSize()
        except:
            import traceback
            print(traceback.print_exc())

    def addSetupEdit(self, setup_file=''):
        try:
            self.btn_delete_list.append(self.createBtn("-", self.index))
            self.btn_file_list.append(self.createBtn(btn_number=self.index))
            self.btn_up_list.append(self.createBtn('↑', self.index))
            self.btn_down_list.append(self.createBtn('↓', self.index))
            self.index += 1
            num = self.getRowCount() - self.getTeardownEditNum() - 3
            self.setup_list.append(PyQt5.QtWidgets.QLineEdit(setup_file))
            self.layout.addWidget(self.setup_list[-1], 2*num, 1, 2, 4)
            self.layout.addWidget(self.btn_file_list[-1], 2*num, 5, 2, 1)
            self.layout.addWidget(self.btn_delete_list[-1], 2*num, 6, 2, 1)
            self.layout.addWidget(self.btn_up_list[-1], 2*num, 7, 2, 1)
            self.layout.addWidget(self.btn_down_list[-1], 2*num, 8, 2, 1)
            num += 1
            self.layout.addWidget(self.btn_add, 2*num, 1, 2, 1)
            num += 1
            self.layout.addWidget(self.teardowns_label, 2*num, 0, 2, 1)
            for i in range(len(self.teardown_list)):
                if self.teardown_list[i]:
                    self.layout.addWidget(self.teardown_list[i], 2*num, 1, 2, 4)
                    self.layout.addWidget(self.btn_teardown_file_list[i], 2*num, 5, 2, 1)
                    self.layout.addWidget(self.btn_teardown_delete_list[i], 2*num, 6, 2, 1)
                    self.layout.addWidget(self.btn_teardown_up_list[i], 2*num, 7, 2, 1)
                    self.layout.addWidget(self.btn_teardown_down_list[i], 2*num, 8, 2, 1)
                    num += 1
            self.layout.addWidget(self.btn_teardown_add, 2*num, 1, 2, 1)
            num += 1
            self.layout.addWidget(self.default, 2*num, 6, 2, 4)
            num += 1
            self.layout.addWidget(self.btn_ok, 2*num, 3, 2, 1)
            self.layout.addWidget(self.btn_cancel, 2*num, 4, 2, 1)
            self.btn_file_list[-1].pressed.connect(self.updateSetup)
            self.btn_delete_list[-1].pressed.connect(self.deleteSetupEdit)
            self.btn_up_list[-1].pressed.connect(self.setupEditUp)
            self.btn_down_list[-1].pressed.connect(self.setupEditDown)
            self.updateSetupEditDownState()
            self.updateSize()
        except:
            import traceback
            print(traceback.print_exc())

    def deleteTeardownEdit(self):
        btn_number = 0
        for i in range(len(self.btn_teardown_delete_list)):
            if self.btn_teardown_delete_list[i] and self.btn_teardown_delete_list[i].isDown():
                btn_number = i
                break
        teardown_file = self.teardown_list[btn_number].text()
        case_dir = self.paras.get('case')
        try:
            if teardown_file and os.sep.join(teardown_file.split(os.sep)[:-2]) == os.path.join(case_dir, 'teardowns'):
                reply = PyQt5.QtWidgets.QMessageBox.question(self, 'Delete Teardowns',
                                                             'Are you sure you want to delete this teardown files ?',
                                                             PyQt5.QtWidgets.QMessageBox.Yes,
                                                             PyQt5.QtWidgets.QMessageBox.No)
                if reply == PyQt5.QtWidgets.QMessageBox.No:
                    return
        except:
            pass
        for btn_list in [self.teardown_list,
                         self.btn_teardown_delete_list,
                         self.btn_teardown_file_list,
                         self.btn_teardown_down_list, self.btn_teardown_up_list]:
            self.layout.removeWidget(btn_list[btn_number])
            btn_list[btn_number].deleteLater()
            btn_list[btn_number] = None
        num = 0
        for btn in self.teardown_list[:btn_number]:
            if btn:
                num += 1
        num += self.getRowCount() - self.getTeardownEditNum() - 2
        for i in range(btn_number + 1, len(self.teardown_list)):
            if self.teardown_list[i]:
                self.layout.addWidget(self.teardown_list[i], 2*num, 1, 2, 4)
                self.layout.addWidget(self.btn_teardown_file_list[i], 2*num, 5, 2, 1)
                self.layout.addWidget(self.btn_teardown_delete_list[i], 2*num, 6, 2, 1)
                self.layout.addWidget(self.btn_teardown_up_list[i], 2*num, 7, 2, 1)
                self.layout.addWidget(self.btn_teardown_down_list[i], 2*num, 8, 2, 1)
                num += 1
        self.layout.addWidget(self.btn_teardown_add, 2*num, 1, 2, 1)
        self.layout.addWidget(self.default, 2 + 2*num, 6, 2, 4)
        num += 1
        self.layout.addWidget(self.btn_ok, 2 + 2*num, 3, 2, 1)
        self.layout.addWidget(self.btn_cancel, 2 + 2*num, 4, 2, 1)
        self.updateSetupEditDownState()
        self.updateSize()

    def deleteSetupEdit(self):
        btn_number = 0
        for i in range(len(self.btn_delete_list)):
            if self.btn_delete_list[i] and self.btn_delete_list[i].isDown():
                btn_number = i
                break
        setup_file = self.setup_list[btn_number].text()
        case_dir = self.paras.get('case')
        try:
            if setup_file and os.sep.join(setup_file.split(os.sep)[:-2]) == os.path.join(case_dir, 'setups'):
                reply = PyQt5.QtWidgets.QMessageBox.question(self, 'Delete Setup',
                                                             'Are you sure you want to delete this setup files ?',
                                                             PyQt5.QtWidgets.QMessageBox.Yes,
                                                             PyQt5.QtWidgets.QMessageBox.No)
                if reply == PyQt5.QtWidgets.QMessageBox.No:
                    return
        except:
            pass
        for btn_list in [self.setup_list,
                         self.btn_delete_list,
                         self.btn_file_list,
                         self.btn_down_list, self.btn_up_list]:
            self.layout.removeWidget(btn_list[btn_number])
            btn_list[btn_number].deleteLater()
            btn_list[btn_number] = None
        num = 0
        for btn in self.setup_list[:btn_number]:
            if btn:
                num += 1
        num += self.getRowCount() - self.getTeardownEditNum() - self.getSetupEditNum() - 2
        for i in range(btn_number + 1, len(self.setup_list)):
            if self.setup_list[i]:
                self.layout.addWidget(self.setup_list[i], 2*num, 1, 2, 4)
                self.layout.addWidget(self.btn_file_list[i], 2*num, 5, 2, 1)
                self.layout.addWidget(self.btn_delete_list[i], 2*num, 6, 2, 1)
                self.layout.addWidget(self.btn_up_list[i], 2*num, 7, 2, 1)
                self.layout.addWidget(self.btn_down_list[i], 2*num, 8, 2, 1)
                num += 1
        self.layout.addWidget(self.btn_add, 2*num, 1, 2, 1)
        num += 1
        self.layout.addWidget(self.teardowns_label, 2*num, 0, 2, 1)
        for i in range(len(self.teardown_list)):
           if self.teardown_list[i]:
               self.layout.addWidget(self.teardown_list[i], 2*num, 1, 2, 4)
               self.layout.addWidget(self.btn_teardown_file_list[i], 2*num, 5, 2, 1)
               self.layout.addWidget(self.btn_teardown_delete_list[i], 2*num, 6, 2, 1)
               self.layout.addWidget(self.btn_teardown_up_list[i], 2*num, 7, 2, 1)
               self.layout.addWidget(self.btn_teardown_down_list[i], 2*num, 8, 2, 1)
               num += 1
        self.layout.addWidget(self.btn_teardown_add, 2*num, 1, 2, 1)
        self.layout.addWidget(self.default, 2 + 2*num, 6, 2, 4)
        num += 1
        self.layout.addWidget(self.btn_ok, 2 + 2*num, 3, 2, 1)
        self.layout.addWidget(self.btn_cancel, 2 + 2*num, 4, 2, 1)
        self.updateSetupEditDownState()
        self.updateSize()

    def getCurrentSetupEditNum(self):
        num = 0
        for btn in self.setup_list:
            if btn:
                num += 1
        return num

    def updateSetupEditDownState(self):
        btn_down_list = list(filter(lambda x:x, self.btn_down_list))
        try:
            btn_down_list[-1].setEnabled(False)
        except:
            pass
        try:
            btn_down_list[-2].setEnabled(True)
        except:
            pass
        btn_up_list = list(filter(lambda x:x, self.btn_up_list))
        try:
            btn_up_list[0].setEnabled(False)
        except:
            pass
   
    def updateTeardownEditDownState(self):
        btn_down_list = list(filter(lambda x:x, self.btn_teardown_down_list))
        try:
            btn_down_list[-1].setEnabled(False)
        except:
            pass
        try:
            btn_down_list[-2].setEnabled(True)
        except:
            pass
        btn_up_list = list(filter(lambda x:x, self.btn_teardown_up_list))
        try:
            btn_up_list[0].setEnabled(False)
        except:
            pass

    def setupEditUp(self):
        btn_up_index = []
        for i in range(len(self.btn_up_list)):
            if self.btn_up_list[i]:
                btn_up_index.append(i)
                if self.btn_up_list[i].isDown():
                    break
        index1, index2 = btn_up_index[-2:]
        setup1 = self.setup_list[index1].text()
        self.setup_list[index1].setText(self.setup_list[index2].text())
        self.setup_list[index2].setText(setup1)

    def setupEditDown(self):
        btn_down_index = []
        for i in range(len(self.btn_down_list)):
            if self.btn_down_list[-1-i]:
                btn_down_index.append(-1-i)
                if self.btn_down_list[-1-i].isDown():
                    break
        index1, index2 = btn_down_index[-2:]
        setup1 = self.setup_list[index1].text()
        self.setup_list[index1].setText(self.setup_list[index2].text())
        self.setup_list[index2].setText(setup1)

    def teardownEditUp(self):
        btn_up_index = []
        for i in range(len(self.btn_teardown_up_list)):
            if self.btn_teardown_up_list[i]:
                btn_up_index.append(i)
                if self.btn_teardown_up_list[i].isDown():
                    break
        index1, index2 = btn_up_index[-2:]
        teardown1 = self.teardown_list[index1].text()
        self.teardown_list[index1].setText(self.teardown_list[index2].text())
        self.teardown_list[index2].setText(teardown1)

    def teardownEditDown(self):
        btn_down_index = []
        for i in range(len(self.btn_teardown_down_list)):
            if self.btn_teardown_down_list[-1-i]:
                btn_down_index.append(-1-i)
                if self.btn_teardown_down_list[-1-i].isDown():
                    break
        index1, index2 = btn_down_index[-2:]
        teardown1 = self.teardown_list[index1].text()
        self.teardown_list[index1].setText(self.teardown_list[index2].text())
        self.teardown_list[index2].setText(teardown1)

    def updateSetup(self):
        btn_number = 0
        for i in range(len(self.btn_file_list)):
            if self.btn_file_list[i] and self.btn_file_list[i].isDown():
                btn_number = i
                break
        setup = self.setFile()
        if setup:
            self.setup_list[btn_number].setText(setup)

    def updateTeardown(self):
        btn_number = 0
        for i in range(len(self.btn_teardown_file_list)):
            if self.btn_teardown_file_list[i] and self.btn_teardown_file_list[i].isDown():
                btn_number = i
                break
        teardown = self.setFile()
        if teardown:
            self.teardown_list[btn_number].setText(teardown)

    def updateSize(self):
        self.height = int(ROW_HEIGHT * self.getRowCount())
        self.setFixedSize(self.width, self.height)

    def getSetupEditNum(self):
        num = 1
        for btn in self.setup_list:
            if btn:
                num += 1
        return num

    def getTeardownEditNum(self):
        num = 1
        for btn in self.teardown_list:
            if btn:
                num += 1
        return num
   
    def getRowCount(self):
        if self.case:
            row_count = len(self.fileinfo_list) \
                        + self.getSetupEditNum() + self.getTeardownEditNum() + 8
        else:
            row_count = len(self.fileinfo_list) + 2.5
        return row_count


if __name__ == '__main__':
    fileinfo_list = [['Path :', 'aaaaa'],
                     ['Type :', 'bbbbb'],
                     ['Size :', 'ccccc'],
                     ['Date Modified :', 'ddddd']
                     ]
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    w = CAttributesSetting(fileinfo_list, r'c:\workspace')
    w.show()
    sys.exit(app.exec_())
