# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-6-19

@author: wushengbing
'''
import sys
from PyQt5.QtWidgets import QApplication, QDockWidget, QTextEdit
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import QPoint


class CWidgetInfo(QDockWidget):
    def __init__(self):
        super(CWidgetInfo, self).__init__()
        self.setWindowTitle('Widget Info')
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.initGui()
                         
    def initGui(self):
        self.editor = QTextEdit(self)
        self.font = QFont("Courier", 12)
        self.editor.setFont(self.font)
        self.editor.setTextColor(QColor(0,0,255))
        
    def editorResize(self):
        self.editor.move(QPoint(0,20))
        x, y = self.width(), self.height()
        self.editor.resize(x, y - 20)
        
    def resizeEvent(self, event):
        self.editorResize()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = CWidgetInfo()
    w.show()
    sys.exit(app.exec_())