# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-7-19

@author: wushengbing
'''
import sys
import os
import copy
from PyQt5.QtCore import *  
from PyQt5.QtGui import *  
from PyQt5.QtWidgets import * 
from .syntaxHighlighter.syntax_highlighter import PythonHighlighter
from . import htmlParser
from ui.common.traceback import trace
from .plainEditor import CPlainEditor
from .richEditor import CRichEditor


class CMultiEditor(QTabWidget):
    statusBarMessageShow = pyqtSignal(str)
    toolbarUpdate = pyqtSignal()

    def __init__(self, parent=None):
        super(CMultiEditor, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle("MultiEditor")
        self.resize(400,400)
        self.font = QFont("Courier", 12)
        self.font.setFixedPitch(True)
        self.tab_index = -1
        self.setTabsClosable(True)
#        self.setElideMode(Qt.ElideLeft)
        self.setUsesScrollButtons(True)
        self.setTabShape(1) # 0:Rounded 1:Triangular
#        self.setTabBarAutoHide(True)
        self.tabCloseRequested.connect(self.closeTable)

        self.edit_dict = {}
        self.highlighter_dict = {}
#        self.editor_type = False  ## False:QTextEdit  True:QsciScintilla
        self.template_paras = {}
        self.editor_type_dict = {}
        self.ctrl_alt_flag = 0

    def closeTable(self, index):
        filename = self.tabToolTip(index)
        if self.currentWidget().change_times > 0:
            reply = QMessageBox.question(self, 
                                'Save File',
                                '%s has been modified.Save changes?' % filename,
                                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save(index, filename)
                self.removeTable(index)
            elif reply == QMessageBox.No:
                self.removeTable(index)
            else:
                #cancel
                pass
        else:
            self.removeTable(index)

    def removeTable(self, index):
        filename = self.tabToolTip(index)
        self.removeTab(index)
        self.tab_index -= 1
        self.toolbarUpdate.emit()
        self.removeEditorType(filename)

    def removeEditorType(self, filename):
        try:
            self.editor_type_dict.pop(filename)
        except:
            pass

    def insertTable(self, index, content, filename, tabname, editor_type):
        self.editor_type_dict[filename] = editor_type
        self.tab_index += 1
        try:
            if editor_type:
                edit = CPlainEditor(self.font, self)
                edit.toolbarUpdate.connect(self.toolbarUpdate)
                self.insertTab(index, edit, tabname)
                self.widget(index).scintilla.setText(content)
            else:
                edit = CRichEditor(self.font, self)
                edit.toolbarUpdate.connect(self.toolbarUpdate)
                highlighter = PythonHighlighter(edit.document())
                self.edit_dict[tabname] = edit
                self.highlighter_dict[tabname] = highlighter
                self.insertTab(index, edit, tabname)
                self.setCurrentIndex(index)
                self.insertContent(content, filename)
            self.setTabToolTip(index, filename)
        except:
            import traceback
            print(traceback.print_exc())

    def getTabName(self, filepath):
        filepath = filepath.replace(os.sep, '/')
        filename = filepath.split('/')[-1].split('.py')[0]
        tab_tips = self.getCurrentTabTips(filename)
        if len(tab_tips) == 0:
            return filename
        else:
            filepath_list = filepath.split('/')
            i = -2
            tab_tips[-1] = filepath
            new_tab_tail = {}
            index_list = list(tab_tips.keys())
            while 1:
                temp_index = []
                for index in index_list:
                    tab_tip = tab_tips[index]
                    tip_name_list = tab_tip.split('/')
                    tail = '.'.join(tip_name_list[i:-1])
                    tail_index = new_tab_tail.get(tail, None)
                    if tail_index is None:
                        new_tab_tail[tail] = index
                    else:
                        if tail_index not in temp_index:
                            temp_index.append(tail_index)
                        temp_index.append(index)
                index_list = copy.deepcopy(temp_index)
                if len(index_list) == 0:
                    break
                i -= 1
        for tail, index in new_tab_tail.items():
            tab_text = filename + "(%s)" % tail
            if index == -1:
                new_tab_name = tab_text
            else:
                self.setTabText(index, tab_text)
        return new_tab_name

    def getCurrentTabTips(self, filename):
        result = {}
        count = self.count()
        for i in range(count):
            filepath = self.tabToolTip(i)
            if filepath.split('/')[-1].split('.py')[0] == filename:
                result[i] = filepath
        return result

    def addTable(self, content, filename, editor_type):
        self.editor_type_dict[filename] = editor_type
        try:
            tab_name = self.getTabName(filename)
            self.tab_index += 1
            if editor_type:
                edit = CPlainEditor(self.font, self)
                edit.toolbarUpdate.connect(self.toolbarUpdate)
                self.addTab(edit, tab_name)
                self.setCurrentIndex(self.tab_index)
                self.currentWidget().scintilla.setText(content)
            else:
                try:
                    edit = CRichEditor(self.font, self)
                    edit.toolbarUpdate.connect(self.toolbarUpdate)
                except:
                    print(traceback.print_exc())
                highlighter = PythonHighlighter(edit.document())
                self.edit_dict[tab_name] = edit
                self.highlighter_dict[tab_name] = highlighter
                self.addTab(edit, tab_name)
                self.setCurrentIndex(self.tab_index)
                self.insertContent(content, filename)
            self.currentWidget().change_times = 0
            self.setTabToolTip(self.tab_index, filename)
        except:
            import traceback
            print(traceback.print_exc())

    def getTabText(self):
        result = {}
        count = self.count()
        for i in range(count):
            tab_name_list = self.tabText(i).split('(')
            tab_name = tab_name_list[0]
            if len(tab_name_list) == 1:
                tab_num = 0
            else:
                tab_num = int(tab_name_list[1].split(')')[0])
            if tab_name in result:
                result[tab_name].append(tab_num)
            else:
                result[tab_name] = [tab_num]
        return result
    
    def getToolTipIndex(self):
        result = {}
        count = self.count()
        for i in range(count):
            tip = self.tabToolTip(i)
            result[tip] = i
        return result
    
    def save(self, index, filename):
        editor_type = self.editor_type_dict[filename]
        if not editor_type:
            file_content = self.widget(index).toHtml()
            file_content = htmlParser.html2text(file_content)
        else:
            file_content = self.widget(index).scintilla.text()
        with open(filename, 'w') as f:
            f.write(file_content)
        self.widget(index).change_times = 0
        self.statusBarMessageShow.emit('save file : %s' % filename)

    def insertContent(self, content, filename):
        image_dir = os.path.dirname(filename).replace('/', os.sep)
        content_list = content.split('\r\n')
        for c in content_list:
            if "Template(" in c:
                tmp_c = c.split('Template(')
                self.currentWidget().append(tmp_c[0])
                
                for j in range(1, len(tmp_c)):
                    brackets_num = 1
                    for i in range(len(tmp_c[j])):
                        if tmp_c[j][i] == '(':
                            brackets_num += 1
                        if tmp_c[j][i] == ')':
                            brackets_num -= 1
                        if brackets_num == 0:
                            index = i
                            break
                    template = tmp_c[j][:index].split(',')
                    for tp in template:
                        if tp.find('.png') > -1 or tp.find('.jpg') > -1:
                            template.remove(tp)
                            if tp.startswith("r'") or tp.startswith('r"'):
                                tp = tp.lstrip('r')
                            tp = tp.strip('"').strip("'")
                            image_name = tp
                            break
                    if len(template) > 0:
                        temp_paras = ','.join(template)
                        if filename not in self.template_paras:
                            self.template_paras[filename] = {}
                        self.template_paras[filename][image_name] = temp_paras
    
                    cursor = self.currentWidget().textCursor()
                    cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
                    cursor.insertHtml("<img src='%s'>" % os.path.join(image_dir, image_name))
                    tail = tmp_c[j][index + 1:]
                    cursor = self.currentWidget().textCursor()
                    cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
                    cursor.insertText(tail)     
            else:
                self.currentWidget().append(c)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    w = CMultiEditor()
    w.show()
    sys.exit(app.exec_())  
