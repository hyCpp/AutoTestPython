# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-5-22

@author: wushengbing
'''
import os
import re
import PyQt5.QtWidgets
import PyQt5.QtGui
import PyQt5.QtCore
from ui.common.traceback import trace
from .. import res


class CWidgetTree(PyQt5.QtWidgets.QDockWidget):
    deviceToolbarUpdate = PyQt5.QtCore.pyqtSignal(list, list)
    screenSizeSet = PyQt5.QtCore.pyqtSignal()
    propertiesShow = PyQt5.QtCore.pyqtSignal(object)
#    zoomFactorUpdate = PyQt5.QtCore.pyqtSignal()
    widgetShow = PyQt5.QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(CWidgetTree, self).__init__()
        self.parent = parent
        self.widget_properties = {}
        self.initGui()
        self.createLayout()
        self.tree_data = {}
        self.setScreenSize()
        self.org_rect = [0,0,0,0]
        self.setWindowTitle('Widget Tree')
        self.setFeatures(PyQt5.QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self.showProperties)
        self.tree.itemClicked.connect(self.showWidget)
        self.text = None
        self.search_index = -1
        self.zoom_factor = 1

    def initGui(self):
        self.widget = PyQt5.QtWidgets.QWidget()
        self.widget.move(PyQt5.QtCore.QPoint(0,15))
        self.widget.setContentsMargins(0,0,0,0)
        self.setContentsMargins(0,0,0,0)
        self.font = PyQt5.QtGui.QFont("Courier", 10)
        self.tree = PyQt5.QtWidgets.QTreeWidget(self.widget)
        self.tree.setColumnCount(1)
        self.tree.setFont(self.font)
        self.btn_search = PyQt5.QtWidgets.QPushButton(self.widget)
        self.btn_search.setIcon(PyQt5.QtGui.QIcon(':/icon/hide.png'))
        self.btn_search.setFixedSize(25,20)
        self.btn_search.setFlat(True)
        self.btn_search.pressed.connect(self.hideSearch)
        self.search = PyQt5.QtWidgets.QLineEdit(self.widget)
        self.search.setPlaceholderText('Search Widget')
        self.search_action = PyQt5.QtWidgets.QAction(PyQt5.QtGui.QIcon(':/icon/search.png'),
                                                     'search', self)
        self.search_action.triggered.connect(self.find_next)
        self.search.returnPressed.connect(self.find_next)
        self.search.addAction(self.search_action,
                              PyQt5.QtWidgets.QLineEdit.TrailingPosition)
#         self.tree.setVerticalScrollBarPolicy(PyQt5.QtCore.Qt.ScrollBarAsNeeded)
        self.tree.setHorizontalScrollBarPolicy(PyQt5.QtCore.Qt.ScrollBarAsNeeded)

    def createLayout(self):
        layout_H = PyQt5.QtWidgets.QHBoxLayout()
        layout_H.addWidget(self.search)
        layout_H.addWidget(self.btn_search)
        self.layout = PyQt5.QtWidgets.QVBoxLayout()
        self.layout.addLayout(layout_H)
        self.layout.addWidget(self.tree)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def hideSearch(self):
        self.search.hide()
        self.btn_search.hide()

    def showSearch(self):
        if self.search.isHidden():
            self.text = None
            self.search_index = -1
            self.search.show()
            self.btn_search.show()
        self.search.clear()

    def getWidgetName(self, payload):
        text_name = payload.get('text')
        if text_name:
            widget_name = text_name
        else:
            class_name = payload.get('className')
            obj_name = payload.get('objectName')
            if class_name and obj_name:
                widget_name = '%s(%s)' % (class_name, obj_name)
            else:
                widget_name = class_name or obj_name or 'node'
        return widget_name

    def getWidgetCaptureName(self, item):
        property = self.properties.get(str(item),[{},None])[0]
        capture_name = self.getWidgetName(property)
#        for s in ['/', '\\', '?']:
#            capture_name = capture_name.replace(s, ' ')
#        capture_name = capture_name.replace('&', 'and').replace('  ', ' ').replace(' ', '_')
        capture_name = re.sub(r'\W', ' ', capture_name)
        capture_name = capture_name.replace('  ', ' ').replace(' ', '_')
        pos = property.get('pos2')
        if pos:
            capture_name += '_%s_%s' % tuple(pos)
        return capture_name

    def __loadTree(self, parent, widget_properties, tree):
        payload = tree.get('payload', None)
        children = tree.get('children',None)
        if payload:
            item = PyQt5.QtWidgets.QTreeWidgetItem(parent, [self.getWidgetName(payload)])
            self.properties[str(item)] = [payload, item]
            rect, org_rect = self.getRect(payload) 
            widget_properties['payload'] = {'org_rect': org_rect,
                                            'item': item}
            if children:
                widget_properties['children'] = []
                for child in children:
                    widget_properties['children'].append({})
                    self.__loadTree(item, widget_properties['children'][-1], child)
        #self.tree.expandAll()

    def setScreenSize(self):
        self.screenSizeSet.emit()

    @trace
    def updateTree(self, tree=None):
        self.tree.clear()
        if tree:
            self.setScreenSize()
            self.tree_data = self.updateTreeData(tree, self.screen_size)
            #if self.tree_data:
            #    self.tree_data['payload']['objectName'] = 'root'
            #    brothers = self.tree_data.get('children')
            #    if brothers and len(brothers) == 2:
            #        brothers[0]['payload']['objectName'] = 'view'
            #        brothers[1]['payload']['objectName'] = 'screen'
            self.widget_properties = {}
            self.properties = {}
            self.__loadTree(self.tree, self.widget_properties, self.tree_data)
            self.deviceToolbarUpdate.emit(['Find Widget'], [True])
            self.search_index = -1
        else:
            self.deviceToolbarUpdate.emit(['Find Widget'], [False])

    @trace
    def showProperties(self, item=None):
        self.propertiesShow.emit(item)

    def getRect(self, layout_dic):
        x, y = layout_dic.get('pos2', (0,0))
        w, h = layout_dic.get('size2', (0,0))
        if x < 0:
            w = w + x
            x = 0
        if y < 0:
            h = h + y
            y = 0
        if w > self.screen_size[0]:
            w = self.screen_size[0]
        if h > self.screen_size[1]:
            h = self.screen_size[1]
#        self.zoomFactorUpdate.emit()
        rect = list(map(lambda k : int(k * self.zoom_factor), [x, y, w, h]))
        return rect, [x, y, w, h]

    @trace
    def showWidget(self, item=None):
        self.widgetShow.emit(item)

    @trace
    def findWidgetFromPoint(self, point, widget_properties=None):
        result = self.findWidgets(point, widget_properties)
#         size = float('inf')
#         index = -1
#         for i in range(len(result)):
#             _, _, w, h = result[i][1]
#             temp_size = w * h
#             if size >= temp_size:
#                 size = temp_size
#                 index = i
#         if index < 0:
#             return [None, None, None]
#         else:
#             return result[index]
        if result:
            return result[-1]
        else:
            return [None, None, None]

    def findWidgetParentFromPoint(self, point, widget_properties=None):
        result = self.findWidgets(point, widget_properties)
        if len(result) > 1:
            _, _, org_rect = result[-1]
            x, y, w, h = org_rect
            i = -2
            while i >= (0 - len(result)):
                _, _, parent_org_rect = result[i]
#                 px, py, pw, ph = parent_org_rect
                if self.isPointInRect(parent_org_rect, (x,y)) \
                    and self.isPointInRect(parent_org_rect, (x+w-1,y+h-1)):
                    return result[i]
                i -= 1
            return [None, None, None]
        else:
            return [None, None, None]

    def findWidgets(self, point, widget_properties=None):
        self.setScreenSize()
        if not widget_properties:
            widget_properties = self.widget_properties
        
        widget_result = []
        children = widget_properties.get('children',None)
        if children:
            for child in children:
                widget_result += self.findWidgets(point, child)
        else:
            payload = widget_properties.get('payload', None)
            if payload:
                if self.isInLayout(payload, point):
                    rect = payload.get('rect', [0,0,0,0])
                    org_rect = payload.get('org_rect', [0,0,0,0])
                    item = payload.get('item', None)
                    #if item.text(0) not in ['###']:
                    if True:
                        #self.zoomFactorUpdate.emit()
                        rect = map(lambda x : round(x * self.zoom_factor), org_rect)
                        widget_result.append((item, rect, org_rect))
        return widget_result

    def findWidgetFromPoint2(self, point, widget_properties=None):
        item = None
        rect = None
        org_rect = [0,0,0,0]
        if not widget_properties:
            widget_properties = self.widget_properties
        payload = widget_properties.get('payload', None)
        children = widget_properties.get('children',None)
        if payload:
            if self.isInLayout(payload, point):
                rect = payload.get('rect', [0,0,0,0])
                org_rect = payload.get('org_rect', [0,0,0,0])
                item = payload.get('item', None)    
                if children:
                    for child in children:
                        result = self.findWidgetFromPoint(point, child)
                        if result[0]:
                            item, rect, org_rect = result
                            break    
        return item, rect, org_rect

    def isInLayout(self, payload, point):
#        self.zoomFactorUpdate.emit()
        x1, y1 = point
        x1 = x1 / self.zoom_factor
        y1 = y1 / self.zoom_factor
        return self.isPointInRect(payload['org_rect'], (x1, y1))

    def isPointInRect(self, rect, point):
        x, y, w, h = rect
        px, py = point
        if px >= x and px < x + w and py >= y and py < y + h:
            return True
        else:
            return False

    @trace
    def updateTreeData(self, tree, screen_size):
        children = tree.get('children',None)
        pos, size = self.calcWidgetSize(tree, screen_size)
        tree['payload']['pos2'] = pos or (0,0)
        tree['payload']['size2'] = size or (0,0)
        if children:
            for child in children:
                self.updateTreeData(child, screen_size)
        return tree

    def calcWidgetSize(self, tree, screen_size):
        result_list = []
        payload = tree.get('payload', None)
        children = tree.get('children',None)
        if payload:
            pos = payload.get('pos', None)
            size = payload.get('size', None)
        if not size or size == (0,0):
            if children:
                for child in children:
                    result_list.append(self.calcWidgetSize(child, screen_size))
                pos, size = self.mergeWidget(result_list)
        else:
            pos = [round(pos[i] * screen_size[i] - size[i] / 2) for i in [0,1]]
        return [pos, size]

    def mergeWidget(self, size_list):
        x1_list = []
        y1_list = []
        x2_list = []
        y2_list = []   
        for pos, size in size_list:
            x1, y1 = pos
            x2 = x1 + size[0]
            y2 = y1 + size[1]
            x1_list.append(x1)
            y1_list.append(y1)
            x2_list.append(x2)
            y2_list.append(y2)
        x, y = round(min(x1_list)), round(min(y1_list))
        width, height = max(x2_list), max(y2_list)
        return [(x, y), (width, height)]

    def findTreeItem(self, text):
        item_list = []
        if text.find('=') == -1:
            for _, item in self.properties.values():
                t = item.text(0)
                if text == t:
                    item_list.append(item)
        else:
            text_list = text.split('=')
            if len(text_list) != 2:
                return item_list
            else:
                key, value = text_list
                value = ''.join(value.split(' '))
                for payload, item in self.properties.values():
                    payload_value = ''.join(str(payload.get(key)).split(' '))
                    if payload_value == value:
                        item_list.append(item)
        return item_list

    def find_next(self):
        text = self.search.text().strip()
        if text != self.text:
            self.search_index = -1
            self.text = text
        if self.search_index < 0:
            self.item_list = self.findTreeItem(text)
            self.search_index += 1
        if not self.item_list:
            self.message("Not found : %s " % self.text)
        else:
            if self.search_index > len(self.item_list) - 1:
                self.message("Reached the end of the tree...")
                self.search_index = 0
            else:
                item = self.item_list[self.search_index]
                self.showProperties(item)
                self.showWidget(item)
                self.search_index += 1

    def message(self, msg):
        PyQt5.QtWidgets.QMessageBox.information(self, 'Find', msg,
                                                PyQt5.QtWidgets.QMessageBox.Ok)


if __name__ == '__main__':
    import sys  
    app = PyQt5.QtWidgets.QApplication(sys.argv)  
    p = CWidgetTree()
    p.show()
#    p.widget.show()
#    p.splitter.show()
    sys.exit(app.exec_())
    