# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-5-10

@author: wushengbing
'''
import sys
import subprocess
import time
import win32gui
import win32api
from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtGui import QWindow
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QWidget,QPushButton
import pythoncom
import pyHook
import threading
from .device import window



class CCatchWindow(QWidget):

    def __init__(self, class_name, window_name, exe_file=None):
        super().__init__()
        self.class_name = class_name
        self.window_name = window_name
        self.exe_file = exe_file
        self.startDevice()
        self.initUI()
        self.hm = pyHook.HookManager()  
        self.hm.MouseLeftDown = self.OnMouseEvent  
        self.hm.HookMouse()
#        pythoncom.PumpMessages(3) 


    def startDevice(self):
        if self.exe_file:
            t = threading.Thread(target=self.runExe, args=(self.exe_file,))
            t.setDaemon(True) 
            t.start()
            t.join() 
        else:
            from multiprocessing import Process
            p = Process(target=window.Do)   
            p.daemon = True
            p.start()
         
    def initUI(self):
        hwnd = win32gui.FindWindowEx(0, 0, self.class_name, self.window_name)
        start = time.time()
        while hwnd == 0:
            time.sleep(0.01)
            hwnd = win32gui.FindWindowEx(0, 0, self.class_name, self.window_name)
            end = time.time()
            if end - start > 5:
                return
        self.window = QWindow.fromWinId(hwnd)
        self.container = self.createWindowContainer(self.window, self)
        window_x, window_y = self.window.width(), self.window.height()
        self.container.resize(window_x, window_y)
        self.resize(window_x, window_y)
        self.setWindowTitle('catchWindow')
        self.show()

        
    def resizeEvent(self, event):
        self.updateWindow()
        
    def updateWindow(self):
        self.window.resize(self.width(), self.height())
#        time.sleep(0.05)
#        self.container.resize(self.window.width(), self.window.height())
        self.update()
        
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                           "Are you sure to quit?",
                                           QMessageBox.Yes,
                                           QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
#            win32api.PostQuitMessage()
            del self.hm
        else:
            event.ignore()
       
    @staticmethod
    def runExe(exe_file):
        subprocess.Popen(exe_file)

    def OnMouseEvent(self, event):
        window_size = (self.size().width(), self.size().height())
        screen_position = event.Position  
        widget_point = self.mapFromGlobal(QPoint(screen_position[0], screen_position[1]))
        widget_position = (widget_point.x(), widget_point.y())
        widget_percent = (widget_point.x()*1.0/window_size[0], 
                          widget_point.y()*1.0/window_size[1])
        if widget_point.x() >= 0 and widget_point.x() <= window_size[0] \
            and widget_point.y() >= 0 and widget_point.y() <= window_size[1]:
            print ('MessageName:',event.MessageName)  
            print ('Message:',event.Message ) 
            print ('Time:',event.Time ) 
            print ('Window:',event.Window)  
            print ('WindowName:',event.WindowName)
            print ('Screen Position:',screen_position)
            print('Widget Position:', widget_position) 
            print('widget percent:', widget_percent)
            print ('Wheel:',event.Wheel  )
            print ('Injected:',event.Injected  )
            print ('---') 
#            try:
#                msg = 'Widget Position: ' + '|'.join(map(str, widget_position))
#            except:
#                pass
#            print(global_queue.queue)
        # 返回 True 可将事件传给其它处理程序，否则停止传播事件  
        return True 






if __name__ == '__main__':
    exe_file = r"C:\Windows\system32\calc.exe"
    app = QApplication(sys.argv)
#    w = CCatchWindow("CalcFrame", "计算器", exe_file)
    w = CCatchWindow("Qt5QWindowIcon", "mydevice")
    sys.exit(app.exec_())   
    