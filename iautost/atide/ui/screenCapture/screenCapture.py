# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-6-11

@author: wushengbing
'''
import os
import sys
import time
import datetime
import threading         
import PyQt5.QtWidgets
import PyQt5.QtGui
import PyQt5.QtCore
from PIL import Image, ImageGrab


class CLabel(PyQt5.QtWidgets.QLabel):
    autoCoding = PyQt5.QtCore.pyqtSignal(str)
#    captureSave = PyQt5.QtCore.pyqtSignal(object)
    captureBoxConvert = PyQt5.QtCore.pyqtSignal(object)
    statusBarMsg = PyQt5.QtCore.pyqtSignal(str)
    caseWindowFileRefresh = PyQt5.QtCore.pyqtSignal(str, object)
    toolBarUpdate = PyQt5.QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(CLabel, self).__init__(parent)
        self.parent = parent
        self.press_flag = False
        self.capture_flag = False
        self.assistant_flag = False
        self.capture_mode = True   ## True : device capture, False : screen capture
        self.capture_auto_naming = False
  
    def paintEvent(self, event):
        PyQt5.QtWidgets.QLabel.paintEvent(self, event)
        try:
            if self.capture_flag and self.press_flag:
                self.painter = PyQt5.QtGui.QPainter()
                self.painter.begin(self)
                self.painter.setBrush(PyQt5.QtGui.QColor(255,0,0, 50))
                self.painter.setPen(PyQt5.QtGui.QColor(255, 0, 255))
                point1 = self.mapFromGlobal(PyQt5.QtCore.QPoint(self.x1, self.y1))
                point2 = self.mapFromGlobal(PyQt5.QtCore.QPoint(self.move_x, self.move_y))
                self.painter.drawRect(point1.x(), point1.y(), 
                                      abs(point2.x() - point1.x()), abs(point2.y() - point1.y()))
                self.painter.end()
            if self.parent.msg:
                self.painter = PyQt5.QtGui.QPainter()
                self.painter.begin(self)
                self.painter.setPen(PyQt5.QtGui.QColor(0, 255, 0))
                w, h = self.parent.w, self.parent.h
                font_size = 50
                while 1:
                    font = PyQt5.QtGui.QFont("Times New Roman",font_size)
                    self.painter.setFont(font)
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

    def mouseMoveEvent(self, event):
        try:
            self.move_x, self.move_y = event.globalX(), event.globalY()
            if self.capture_flag and self.press_flag:
                self.repaint()        
        except:
            import traceback
            traceback.print_exc()

    def mousePressEvent (self, event):
        if self.capture_flag:
            if event.button() == PyQt5.QtCore.Qt.RightButton:
                self.parent.setCaptureState(False)
                self.parent.close()
            if self.capture_flag and event.button() == PyQt5.QtCore.Qt.LeftButton:
                self.x1, self.y1 = event.globalX(), event.globalY()
                self.press_flag = True

    def mouseReleaseEvent (self, event):
        if self.capture_flag and self.press_flag:
            if event.button() == PyQt5.QtCore.Qt.LeftButton:
                self.x2, self.y2 = event.globalX(), event.globalY()
            self.box = (self.x1, self.y1, self.x2, self.y2)
            self.press_flag = False
            self.__capture()

    def __capture(self):
        self.parent.capture_file = None
        self.repaint()
        if self.box[:2] == self.box[2:]:
            return
        if self.capture_mode:
            image = Image.open('ui/screenCapture/screen/current_screen.jpg')
            valid_flag, box = self.parent.convertCaptureBox(image.size)
            if valid_flag:
                image = image.crop(box)
            else:
                PyQt5.QtWidgets.QMessageBox.information(self,
                                                        'Capture',
                                                        'your capture region is not in device, please capture again...',
                                                        PyQt5.QtWidgets.QMessageBox.Ok)
                self.parent.capture_file = 'invald_region.png'
                return
        else:
            image = Image.open('ui/screenCapture/screen/screen.png')
            image = image.crop(self.box)
        if self.capture_auto_naming:
            file_dir = self.case_dir[:self.case_dir.rfind('/')]
            filename =  os.path.join(file_dir,
                                     'capture_%s.png' % datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'))
            filename = filename.replace(os.sep, '/')
        else:
            filename, _ = PyQt5.QtWidgets.QFileDialog.getSaveFileName(self,
                                                                      'Save Screen Capture File',
                                                                      self.case_dir, "Image(*.png)")
        if filename:
            image.save(filename)
            if not self.assistant_flag:
                self.autoCoding.emit(filename)
            self.statusBarMsg.emit('ScreenCapture: %s' % filename)
            self.caseWindowFileRefresh.emit(os.sep.join(filename.split('/')[:-1]), False)
        self.parent.setCaptureState(False)
        self.parent.capture_file = filename


class CCaptureWindow(PyQt5.QtWidgets.QDialog):
    toolBarUpdate = PyQt5.QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(CCaptureWindow, self).__init__()
        self.initUI()
        self.parent = parent
        self.msg = ''
        self.capture_flag = False
        self.capture_file = None
#        self.showFullScreen()

    def initUI(self):
        self.setWindowTitle('Capture Window')
        self.setWindowFlags(PyQt5.QtCore.Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.screen = CLabel(self)
        self.screen.setScaledContents(True)
        self.adjustSize()

    def setScreen(self, screenshot='ui/screenCapture/screen/mask.png'):
        self.pixmap = PyQt5.QtGui.QPixmap(screenshot)
        self.w, self.h = self.pixmap.width(), self.pixmap.height()
        self.screen.setPixmap(self.pixmap)
        self.screen.resize(self.w, self.h)
        self.resize(self.w, self.h)

    def setCaptureState(self, state=True):
        if state:
            self.screen.capture_flag = True
        else:
            self.unsetCursor()
            self.screen.capture_flag = False
            self.toolBarUpdate.emit()
            self.close()

    def keyPressEvent(self, event):
        if event.key() == PyQt5.QtCore.Qt.Key_Escape:
            self.setCaptureState(False)
            self.close()
        else:
            PyQt5.QtWidgets.QWidget.keyPressEvent(self, event)
            
    def capture(self, capture_auto_naming):
        self.device.pixmap.save('ui/screenCapture/screen/current_screen.jpg')
        try:
            img= ImageGrab.grab()
            img.save('ui/screenCapture/screen/screen.png')
            x, y = img.size
            mask = Image.new('RGBA', (x, y), (200, 200, 200, 128))
            img.paste(mask, (0,0), mask)
            img.save('ui/screenCapture/screen/mask.png')
        except:
            import traceback
            print(traceback.print_exc())
        self.setScreen('ui/screenCapture/screen/mask.png')
        self.screen.capture_flag = True
        self.screen.capture_auto_naming = capture_auto_naming
        self.setCursor(PyQt5.QtCore.Qt.CrossCursor)
        self.exec_()

    def setDevice(self, device):
        self.device = device

    def convertCaptureBox(self, image_size):
        x1, y1, x2, y2 = self.screen.box
        point1 = self.device.screen.mapFromGlobal(PyQt5.QtCore.QPoint(x1, y1))
        point2 = self.device.screen.mapFromGlobal(PyQt5.QtCore.QPoint(x2, y2))
        scale = self.device.getScale()
        box = list(map(lambda x: int(x / scale),
                       [point1.x(), point1.y(), point2.x(), point2.y()]))
        for i in range(len(box)):
            index = i % 2
            if box[i] < 0:
                box[i] = 0
            if box[i] >= image_size[index]:
                box[i] = image_size[index] - 1
        self.screen.box = box
        width = box[2] - box[0]
        height = box[3] - box[1]
        if width > 0 and height > 0:
            valid_flag = True
        else:
            valid_flag = False
        return [valid_flag, box]

            