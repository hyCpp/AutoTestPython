# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-6-11

@author: wushengbing
'''
import os
import sys
import time
import threading         
import PyQt5.QtWidgets
import PyQt5.QtGui
import PyQt5.QtCore
from PIL import Image, ImageGrab


class CLabel(PyQt5.QtWidgets.QLabel):

    def __init__(self, parent=None):
        super(CLabel, self).__init__(parent)
        self.parent = parent

    def paintEvent(self, event):
        PyQt5.QtWidgets.QLabel.paintEvent(self, event)
        try:
            self.painter = PyQt5.QtGui.QPainter()
            self.painter.begin(self)
            self.painter.setPen(PyQt5.QtGui.QColor(0, 255, 0))
            w, h = self.parent.w, self.parent.h
            font_size = 50
            while 1:
                font = PyQt5.QtGui.QFont("Times New Roman",font_size)
                self.painter.setFont(font)
#                y = h // 2 - PyQt5.QtGui.QFontMetrics(font).height() // 2
                y = PyQt5.QtGui.QFontMetrics(font).height() 
                x = w // 2 - PyQt5.QtGui.QFontMetrics(font).width(self.parent.msg) // 2
                if x < 0:
                    font_size -= 2
                else:
                    break
            self.painter.drawText(PyQt5.QtCore.QPoint(x,y), self.parent.msg)
            self.painter.end()
        except:
            import traceback
            traceback.print_exc()       


class CMsg(PyQt5.QtWidgets.QDialog):

    def __init__(self, parent=None, msg=''):
        super(CMsg, self).__init__()
        self.parent = parent
        self.msg = msg
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Message')
        self.setWindowFlags(PyQt5.QtCore.Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.screen = CLabel(self)
        self.screen.setScaledContents(True)
        self.adjustSize()

    def setScreen(self, screenshot='ui/screenCapture/screen/screen.png'):
        self.pixmap = PyQt5.QtGui.QPixmap(screenshot)
        self.w, self.h = self.pixmap.width(), self.pixmap.height()
        self.screen.setPixmap(self.pixmap)
        self.screen.resize(self.w, self.h)
        self.resize(self.w, self.h)

    def showMsg(self):
        try:
            img= ImageGrab.grab()
            img.save('ui/screenCapture/screen/screen.png')
            x, y = img.size
        except:
            import traceback
            print(traceback.print_exc())
        self.setScreen()
        import threading
        t = threading.Thread(target=self.closeMsg, args=(1.0,))
        t.start()
        self.exec_()

    def closeMsg(self, t):
        time.sleep(t)
        self.reject()

