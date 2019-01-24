# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-10-8

@author: wushengbing
'''
import sys, os
import json
import PyQt5.QtWidgets
import PyQt5.QtGui
import PyQt5.QtCore
import autost.api
try:
    from . import caseAttributesSetting
except:
    import caseAttributesSetting


class CCase(caseAttributesSetting.CAttributesSetting):
    
    def __init__(self, current_dir=os.getcwd()):
        super(CCase, self).__init__()
        self.width = 700
        self.case_dir = None
        self.case_name_flag = True
        self.setWindowTitle('New Case')
        self.setFixedWidth(self.width)
        self.current_dir = current_dir
        self.initGui()
        self.createLayout()
        self.btn_add.pressed.connect(self.addSetupEdit)
        self.btn_teardown_add.pressed.connect(self.addTeardownEdit)
        self.btn_ok.pressed.connect(self.ok)
        self.btn_cancel.pressed.connect(self.cancel)
        self.btn_case_file.pressed.connect(self.setCase)
        self.case_name.textChanged.connect(self.checkCaseName)

    def initGui(self):
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
        self.case_label =  PyQt5.QtWidgets.QLabel('CaseDir:')
        self.case = PyQt5.QtWidgets.QLineEdit(self.current_dir)
        self.btn_case_file = self.createBtn()
        self.case_name_label = PyQt5.QtWidgets.QLabel('CaseName :')
        self.case_name = PyQt5.QtWidgets.QLineEdit()
        self.case_name_desc = PyQt5.QtWidgets.QLabel()
        self.case_name_desc.setStyleSheet('QLabel{color:red}')
        self.setups_label = PyQt5.QtWidgets.QLabel('Setups :')
        self.teardowns_label = PyQt5.QtWidgets.QLabel('Teardowns :')
        self.btn_add = self.createBtn("+")
        self.btn_teardown_add = self.createBtn("+")
        self.btn_ok = PyQt5.QtWidgets.QPushButton('OK')
        self.btn_cancel = PyQt5.QtWidgets.QPushButton('Cancel')
        self.createTemplateBtn()

    def createLayout(self):
        index = 0
        self.layout = PyQt5.QtWidgets.QGridLayout()
        widget_list = [[self.case_name_label, self.case_name],
                        [self.case_label, self.case, self.btn_case_file],
                        [self.createLine()],
                        [self.setups_label, self.btn_add],
                        [self.teardowns_label,self.btn_teardown_add]
                        ]
        for widgets in widget_list:
            if len(widgets) == 1:
                self.layout.addWidget(widgets[0], index, 0, 2, 10)
            else:
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
        self.layout.addWidget(self.default, index, 5, 2, 1)
        index += 2
        self.layout.addWidget(self.btn_ok, index, 3, 2, 1)
        self.layout.addWidget(self.btn_cancel, index, 4, 2, 1)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 2)
        self.layout.setColumnStretch(2, 2)
        self.setLayout(self.layout)
        self.case_name.setFocus()
        self.btn_ok.setDefault(True)
        self.layout.addWidget(self.case_name_desc, 0, 5, 2, 5)

    def checkCaseName(self):
        case_name = self.case_name.text().strip()
        if not case_name:
            return
        if case_name.endswith('.air'):
            case_name = case_name[:-4]
        try:
            __import__(case_name)
            self.case_name_flag = False
        except:
            self.case_name_flag = True
        if not self.case_name_flag:
            self.case_name.setStyleSheet('QLineEdit{color:red}')
            self.case_name_desc.setText('invalid case name')
        else:
            self.case_name.setStyleSheet('QLineEdit{color:black}')
            self.case_name_desc.clear()

    def ok(self):
        case_dir = self.case.text().strip()
        case_name = self.case_name.text().strip()
        if case_dir and case_name:
            if not self.case_name_flag:
                PyQt5.QtWidgets.QMessageBox.information(self,'New Case',
                                                        'The CaseName is invalid, please rename the new case...',
                                                        PyQt5.QtWidgets.QMessageBox.Ok,
                                                        PyQt5.QtWidgets.QMessageBox.Cancel)
                return
            case_dir = case_dir.replace('/', os.sep)
            case_name = case_name.replace('/', os.sep)
            if not case_name.endswith('.air'):
                case_name = case_name + '.air'
            self.case_dir = os.path.join(case_dir, case_name)
            if os.path.exists(self.case_dir):
                PyQt5.QtWidgets.QMessageBox.information(self,'New Case',
                                                        'This case already exists, please rename the new case...',
                                                        PyQt5.QtWidgets.QMessageBox.Ok,
                                                        PyQt5.QtWidgets.QMessageBox.Cancel)
                return
            os.makedirs(self.case_dir)
            self.paras['case'] = self.case_dir
            dir = self.case_dir.split(os.sep)
            filename = dir[-1].split('.')[0] + '.py'
            self.filepath = os.sep.join(dir + [filename])
            with open(self.filepath, 'w') as f:
                f.write('from autost.api import *\n\n')
            self.updateSetupTeardown()
        else:
            PyQt5.QtWidgets.QMessageBox.information(self,'New Case',
                                                    'Please input CaseDir and CaseName...',
                                                    PyQt5.QtWidgets.QMessageBox.Ok,
                                                    PyQt5.QtWidgets.QMessageBox.Cancel)

    def getRowCount(self):
        row_count = self.getSetupEditNum() + self.getTeardownEditNum() + 5
        return row_count

    def setCase(self):
        dirname = PyQt5.QtWidgets.QFileDialog.getExistingDirectory(self, 'Set Case Dir',
                                                                   self.current_dir,
                                                                   PyQt5.QtWidgets.QFileDialog.ShowDirsOnly)
        if dirname:
            dirname = dirname.replace('/', os.sep)
            self.case.setText(dirname)

    def loadTemplate(self):
        try:
            configs = json.load(open('ui/caseManager/template.json'))
        except:
            configs = {}
        for config_type in ('setups', 'teardowns'):
            files = configs.get(config_type, [])
            abs_files = [self.getAbsPath(s, os.getcwd()) for s in files]
            for f in abs_files:
                if config_type == 'setups':
                    self.addSetupEdit(f)
                else:
                    self.addTeardownEdit(f)


if __name__ == '__main__':
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    w = CCase()
    w.exec_()
    sys.exit(app.exec_())        
        
        
        
        