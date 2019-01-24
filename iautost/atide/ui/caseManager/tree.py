# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-7-24

@author: wushengbing
'''
import os
import PyQt5.QtWidgets
import traceback


class CTreeView(PyQt5.QtWidgets.QTreeView):
    currentIndexSet = PyQt5.QtCore.pyqtSignal(object)
    selectionSet = PyQt5.QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(CTreeView, self).__init__()
        self.parent = parent
        self.shift_flag = False
        if self.parent:
            self.currentIndexSet.connect(self.parent.setCurrentIndex)
            self.selectionSet.connect(self.parent.setSelection)

    def dropEvent(self, event):
        try:
            target_index = self.indexAt(event.pos())
            if target_index:
                if self.model().fileInfo(target_index).isDir():
                    target_dir = self.model().filePath(target_index)
                else:
                    target_dir = self.model().filePath(target_index.parent())
                target_dir = target_dir.replace('/', os.sep)
            else:
                return
            selected_index = self.selectedIndexes()
            for s in selected_index:
                if self.model().fileInfo(s).isDir():
                    continue
                selected_file = self.model().filePath(s).replace('/', os.sep)
                selected_dir = self.model().filePath(s.parent()).replace('/', os.sep)
                if selected_dir == target_dir:
                    continue
                self.copyIndex(selected_file, target_dir)
        except:
            print(traceback.print_exc())

    def copyIndex(self, src_file, dest_dir):
        try:
            self.parent.copy_file_list = [src_file]
            self.parent.paste(dest_dir)
        except:
            print(traceback.print_exc())

    def mousePressEvent (self, event):
        if self.shift_flag:
            self.clearSelection()
        PyQt5.QtWidgets.QTreeView.mousePressEvent(self, event)
        if event.button() == PyQt5.QtCore.Qt.LeftButton:
            try:
                if self.shift_flag:
                    self.currentIndexSet.emit(self.currentIndex())
                    self.selectionSet.emit()
            except:
                pass

    def keyPressEvent(self, event):
        if event.key() == PyQt5.QtCore.Qt.Key_Shift:
            current_index = self.currentIndex()
            self.setMultiSelection(True)
            self.shift_flag = True
            self.currentIndexSet.emit(current_index)
        elif event.key() == PyQt5.QtCore.Qt.Key_Control:
            self.setMultiSelection(True)
        else:
            PyQt5.QtWidgets.QTreeView.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        if event.key() == PyQt5.QtCore.Qt.Key_Shift:
            self.shift_flag = False
            self.setMultiSelection(False)
            self.currentIndexSet.emit(None)
        elif event.key() == PyQt5.QtCore.Qt.Key_Control:
            self.setMultiSelection(False)
        else:
            PyQt5.QtWidgets.QTreeView.keyReleaseEvent(self, event)

    def setMultiSelection(self, flag=True):
        if flag:
            self.setSelectionMode(PyQt5.QtWidgets.QAbstractItemView.MultiSelection)
        else:
            self.setSelectionMode(PyQt5.QtWidgets.QAbstractItemView.SingleSelection)
