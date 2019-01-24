# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-7-24

@author: wushengbing
'''
import PyQt5.QtWidgets
import PyQt5.QtCore


class CDirModel(PyQt5.QtWidgets.QDirModel):###QFileSystemModel

    def __init__(self):
        super(CDirModel, self).__init__()
        self.checkedIndexes = set()
        self.multi_case_select = False

    def headerData(self, section, orientation, role):
        if role != PyQt5.QtCore.Qt.DisplayRole:
            return PyQt5.QtCore.QVariant()
        if orientation == PyQt5.QtCore.Qt.Horizontal:
            section_dict = {0:'Case Manager', 1:'Size', 2:'Type', 3:'Date Modified'}
            return section_dict[section]
        return PyQt5.QtCore.QAbstractItemModel.headerData(section, orientation, role)

    def flags(self, index):
        filename = self.fileName(index)
        if self.fileInfo(index).isDir() and filename.split('.')[-1] == 'air':
            return PyQt5.QtWidgets.QDirModel.flags(self, index) | PyQt5.QtCore.Qt.ItemIsUserCheckable \
                | PyQt5.QtCore.Qt.ItemIsEditable
        elif self.fileInfo(index).isDir() and self.fileName(index) == '__pycache__':
            return PyQt5.QtCore.Qt.ItemIsTristate
        else:
            return PyQt5.QtWidgets.QDirModel.flags(self, index) \
                        | PyQt5.QtCore.Qt.ItemIsDragEnabled | PyQt5.QtCore.Qt.ItemIsDropEnabled \
                        | PyQt5.QtCore.Qt.ItemIsEditable

    def data(self, index, role):
        if self.fileInfo(index).isDir() and self.fileName(index).split('.')[-1] == 'air':
            if role == PyQt5.QtCore.Qt.CheckStateRole and self.multi_case_select:
                if index in self.checkedIndexes:
                    return PyQt5.QtCore.Qt.Checked
                else:
                    return PyQt5.QtCore.Qt.Unchecked
            else:
                return PyQt5.QtWidgets.QDirModel.data(self, index, role)
        elif self.filePath(index).find('__pycache__') > -1:
            filelist = self.filePath(index).split('/')
            if '__pycache__' in filelist:
                return False
            else:
                return PyQt5.QtWidgets.QDirModel.data(self, index, role)
        else:
            return PyQt5.QtWidgets.QDirModel.data(self, index, role)

    def setData(self, index, value, role):
        if role == PyQt5.QtCore.Qt.CheckStateRole:
            if value == PyQt5.QtCore.Qt.Checked:
                self.checkedIndexes.add(index)
                if self.hasChildren(index):
                    self.checkChildren(index, value)
            else:
                self.checkedIndexes.remove(index)
                if self.hasChildren(index):
                    self.checkChildren(index, value)
            return True

        return PyQt5.QtWidgets.QDirModel.setData(self, index, value, role)

    def checkChildren(self, index, value):
        return
        count = self.rowCount(index)
        for i in range(count):
            child = PyQt5.QtWidgets.QDirModel.index(self, i, 0, index)
            self.setData(child, value, PyQt5.QtCore.Qt.CheckStateRole)
            
