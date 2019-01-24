# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-5-22

@author: wushengbing
'''
import sys
import PyQt5.QtWidgets
import PyQt5.QtCore
from PyQt5.QtWidgets import QApplication
from ui.common.defaultWindow import CDefaultWindow
from . import res


class CShell(CDefaultWindow):
    stopRun = PyQt5.QtCore.pyqtSignal()
     
    def __init__(self):
        super(CShell, self).__init__()
        self.setWindowTitle('Shell')
        self.edit = PyQt5.QtWidgets.QTextEdit(self)
        self.edit.move(PyQt5.QtCore.QPoint(0,20))
        self.createToolbar()

    def clear(self):
        self.edit.clear()
        
    def resizeEvent(self, event):
        self.updateWindow()
        
    def updateWindow(self):
        w, h = self.size().width(), self.size().height()
        if h > 20 :
            self.edit.resize(w, h-20)
        else:
            self.edit.resize(w, h)
        self.toolbar.move(PyQt5.QtCore.QPoint(w-50,-2))
     
    def createToolbar(self):
        self.toolbar = PyQt5.QtWidgets.QToolBar(self)
        self.action = PyQt5.QtWidgets.QAction(PyQt5.QtGui.QIcon(':/icon/stop.png'),
                                              'Terminate', self)
        self.action.triggered.connect(self.terminate)
        self.toolbar.addAction(self.action)
        self.toolbar.resize(25,25)
        self.action.setEnabled(False)

    def terminate(self):
        self.action.setEnabled(False)
        self.stopRun.emit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = CShell()
    w.show()
    sys.exit(app.exec_())    