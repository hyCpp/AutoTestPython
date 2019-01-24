# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-7-24

@author: wushengbing
'''
import sys
import os
import PyQt5.QtWidgets
import PyQt5.QtGui


class CButton(PyQt5.QtWidgets.QPushButton):

    def __init__(self, text, btn_number=0):
        super(CButton, self).__init__(text)
        self.btn_number = btn_number


class CConfig(PyQt5.QtWidgets.QDialog):
    
    def __init__(self, case="", device="iauto:///"):
        super(CConfig, self).__init__()
        self.paras = {'case' : case,
                      'device' : device}
        self.font = PyQt5.QtGui.QFont("SimSun",10) #"微软雅黑",10  "Courier", 12  
        self.setFont(self.font)

    def init(self):
        self.initGui()
        self.createLayout()
        self.setWindowTitle('Multi Run Config...')
        self.btn_ok.pressed.connect(self.updateParas)
        self.btn_cancel.pressed.connect(self.close)
        self.btn_dir.pressed.connect(self.setLogDir)
        self.btn_casedir.pressed.connect(self.setCaseDir)
        
    def initGui(self):
        self.case_label = PyQt5.QtWidgets.QLabel('Case   :')
        self.case = PyQt5.QtWidgets.QLineEdit(self.paras.get('case'))
#        self.case.setTextInteractionFlags(PyQt5.QtCore.Qt.TextSelectableByMouse)
        self.device_label = PyQt5.QtWidgets.QLabel('Device :')
        self.device = PyQt5.QtWidgets.QLineEdit(self.paras.get('device'))
        self.rounds = PyQt5.QtWidgets.QLineEdit('1')
        self.rounds_label =  PyQt5.QtWidgets.QLabel('Rounds :')
        case_dir = self.paras.get('case')
        if case_dir.endswith('.air'):
            logdir = os.path.join(case_dir, 'log')
        else:
            logdir = case_dir
        self.logdir = PyQt5.QtWidgets.QLineEdit(logdir)
        self.logdir_label = PyQt5.QtWidgets.QLabel('Logdir :')
        self.btn_ok = PyQt5.QtWidgets.QPushButton('OK')
        self.btn_cancel = PyQt5.QtWidgets.QPushButton('Cancel')
        width = max(35,len(self.paras.get('device')), 
                    len(self.paras.get('case'))) *10 + 50
        self.setFixedSize(width,180)
        self.btn_dir = self.createBtn()
        self.btn_casedir = self.createBtn()

    def createLayout(self):
        self.layout = PyQt5.QtWidgets.QGridLayout()
        self.layout.addWidget(self.case_label, 0, 0, 2, 1)
        self.layout.addWidget(self.case, 0, 1, 2, 4)
        self.layout.addWidget(self.btn_casedir, 0, 5, 2, 1)
        self.layout.addWidget(self.device_label, 2, 0, 2, 1)
        self.layout.addWidget(self.device, 2, 1, 2, 4)
        self.layout.addWidget(self.logdir_label, 4, 0, 2, 1)
        self.layout.addWidget(self.logdir, 4, 1, 2, 4)
        self.layout.addWidget(self.btn_dir, 4, 5, 2, 1)
        self.layout.addWidget(self.rounds_label, 6, 0, 2, 1)
        self.layout.addWidget(self.rounds, 6, 1, 2, 1)
        self.layout.addWidget(self.btn_ok, 8, 2, 1, 1)
        self.layout.addWidget(self.btn_cancel, 8, 3, 1, 1)
        self.setLayout(self.layout)

    def setParas(self, name, value):
        self.paras[name] = value

    def updateParas(self):
        self.paras['rounds'] = int(self.rounds.text())
        self.paras['logdir'] = self.logdir.text()
        self.paras['device'] = self.device.text()
        self.paras['case'] = self.case.text()
        self.close()

    def cancel(self):
        self.paras = {}
        self.close()
    
    def setLogDir(self):
        dirname = self.setDir()
        self.logdir.setText(dirname)
        
    def setCaseDir(self):
        dirname = self.setDir()
        self.case.setText(dirname)

    def setDir(self):
        PWD = os.getcwd() + os.sep + 'workspace'
        dirname = PyQt5.QtWidgets.QFileDialog.getExistingDirectory(self, 'Set Directory',
                                                                   PWD,
                                                                   PyQt5.QtWidgets.QFileDialog.ShowDirsOnly)
        dirname = dirname.replace('/', os.sep)
        return dirname
    
    def setFile(self):
        PWD = os.getcwd() + os.sep + 'workspace'
        filename, _= PyQt5.QtWidgets.QFileDialog.getOpenFileName(self, 'Set File',
                                                                 PWD,
                                                                "Python Files(*.py)")
        filename = filename.replace('/', os.sep)
        return filename
    
    def createBtn(self, name="...", btn_number=0):
        btn = CButton(name, btn_number)
        btn.setFixedSize(30,23)
        return btn


if __name__ == '__main__':
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    w = CConfig('C:\workspace\source\source\workspace\T0', '')
    w.init()
    w.show()
    sys.exit(app.exec_())
