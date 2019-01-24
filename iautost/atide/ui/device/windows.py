# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-10-29

@author: wushengbing
'''
import sys
import subprocess
import time
import PyQt5.QtGui
import PyQt5.QtWidgets


class CWindows(PyQt5.QtWidgets.QDockWidget):
    def __init__(self, hwnd):
        super(CWindows, self).__init__()
        self.hwnd = hwnd
        self.initGui()
        self.setWindowTitle('My Device')
        self.setWindowFlags(PyQt5.QtCore.Qt.FramelessWindowHint)
        self.setFeatures(PyQt5.QtWidgets.QDockWidget.NoDockWidgetFeatures)

    def initGui(self):
        self.window = PyQt5.QtGui.QWindow.fromWinId(self.hwnd)
        self.container = self.createWindowContainer(self.window, self)
        self.container.move(PyQt5.QtCore.QPoint(0,30))
        window_x, window_y = self.window.width(), self.window.height()
        if window_x > 800:
            window_x = 800
        if window_y > 800:
            window_y = 800
        self.window.resize(window_x, window_y)
        self.container.resize(window_x, window_y)
        self.resize(window_x, window_y)

    def resizeEvent(self, event):
        self.updateWindow()

    def updateWindow(self):
        self.window.resize(self.width(), self.height())
#        self.container.resize(self.window.width(), self.window.height())
        self.update()

if __name__ == '__main__':
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    w = CWindows(2098966)
    w.show()
    sys.exit(app.exec_())
