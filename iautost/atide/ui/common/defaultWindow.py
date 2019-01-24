# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-5-22

@author: wushengbing
'''
import sys
from PyQt5.QtWidgets import QApplication, QFrame, QDockWidget


def traceback(f):
    def func(*args, **kwargs):
        try:
            try:
                r = f(*args, **kwargs)
            except:
                r = f(args[0])
        except:
            import traceback
            print('function : %s' % f)
            print(traceback.print_exc())
        return r
    return func


class CDefaultWindow(QDockWidget):
    def __init__(self):
        super(CDefaultWindow, self).__init__()
#        self.setFrameStyle(QFrame.StyledPanel)
        self.setWindowTitle('Default Window')
        self.resize(400,400)
#        self.setFeatures(QDockWidget.DockWidgetClosable)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
#        self.setFeatures(QDockWidget.DockWidgetFloatable)
#        self.setFeatures(QDockWidget.DockWidgetMovable)

        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = CDefaultWindow()
    w.show()
    sys.exit(app.exec_())  