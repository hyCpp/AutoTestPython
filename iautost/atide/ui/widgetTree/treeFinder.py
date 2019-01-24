# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-6-26

@author: wushengbing
'''
import sys
import PyQt5.QtWidgets
import PyQt5.QtGui
from ui.common.traceback import trace
from .. import res

class CTreeFinder(PyQt5.QtWidgets.QDialog):

    def __init__(self, widget_tree=None):
        super(CTreeFinder, self).__init__()
        self.widget_tree = widget_tree
        self.setWindowTitle('Find Tree Node')
        self.setWindowIcon(PyQt5.QtGui.QIcon(':/icon/tree.png'))
        self.setFixedSize(400,120)
        self.initGui()
        self.loadTreeData()
        self.btn_next.pressed.connect(self.find_next)
        self.btn_prev.pressed.connect(self.find_prev)
        self.createLayout()

    def initGui(self):
        self.label = PyQt5.QtWidgets.QLabel('Find :')
        self.editor = PyQt5.QtWidgets.QLineEdit()
        self.btn_prev = PyQt5.QtWidgets.QPushButton('Prev')
        self.btn_next = PyQt5.QtWidgets.QPushButton('Next')

    def createLayout(self):
        self.layout = PyQt5.QtWidgets.QGridLayout()
        self.layout.addWidget(self.label, 1,0,1,1)
        self.layout.addWidget(self.editor, 1,1,1,3)
        self.layout.addWidget(self.btn_next, 2,4,1,1)
        self.layout.addWidget(self.btn_prev, 0,4,1,1)
        self.setLayout(self.layout)

    def loadTreeData(self):
        self.index = -1
        self.tree_data = {}
        self.text = None
        if self.widget_tree:
            for k in list(self.widget_tree.properties.values()):
                item = k[1]
                t = item.text(0)
                if self.tree_data.get(t):
                    self.tree_data[t].append(item)
                else:
                    self.tree_data[t] = [item]

    def findTreeItem(self, text):
        if text.find('=') == -1:
            item_list = self.tree_data.get(text, [])
        else:
            text_list = text.split('=')
            if len(text_list) != 2:
                item_list = []
            else:
                item_list = []
                key, value = text_list
                value = ''.join(value.split(' '))
                for payload, item in self.widget_tree.properties.values():
                    payload_value = ''.join(str(payload.get(key)).split(' '))
                    if payload_value == value:
                        item_list.append(item)
        return item_list

    @trace
    def find_prev(self):
        text = self.editor.text().strip()
        if text != self.text:
            self.index = -1
            self.text = text
        if self.index < 0:
            self.item_list = self.findTreeItem(text)
            self.index += 1
        if not self.item_list:
            self.message("Not found : %s " % self.text)
        else:
            self.index -= 1
            if self.index < 0:
                self.message("Reached the end of the tree...")
            else:
                item = self.item_list[self.index]
                self.widget_tree.showProperties(item)
                self.widget_tree.showWidget(item)

    @trace
    def find_next(self):
        text = self.editor.text().strip()
        if text != self.text:
            self.index = -1
            self.text = text
        if self.index < 0:
            self.item_list = self.findTreeItem(text)
            self.index += 1
        if not self.item_list:
            self.message("Not found : %s " % self.text)
        else:
            if self.index > len(self.item_list) - 1:
                self.message("Reached the end of the tree...")
            else:
                item = self.item_list[self.index]
                self.widget_tree.showProperties(item)
                self.widget_tree.showWidget(item)
                self.index += 1

    def message(self, msg):
        PyQt5.QtWidgets.QMessageBox.information(self, 'Find', msg,
                                                PyQt5.QtWidgets.QMessageBox.Ok)

