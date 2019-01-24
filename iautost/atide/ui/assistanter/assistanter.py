# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-9-13

@author: wushengbing
'''
import sys
from inspect import signature
from queue import Queue
import PyQt5.QtWidgets
import PyQt5.QtCore
import PyQt5.QtGui
from PyQt5.QtWidgets import QApplication
try:
    from common.defaultWindow import CDefaultWindow
except:
    from ui.common.defaultWindow import CDefaultWindow
from ui import res
from ui.deviceController import REC
from autost.api import *
from . import assistanterMsg, tboxCommand


class CSelection(PyQt5.QtWidgets.QDialog):
    def __init__(self, title, selection_list, double_column=False):
        super(CSelection, self).__init__()
        self.title = title
        self.selection_list = selection_list
        self.setWindowTitle(self.title)
        self.setWindowIcon(PyQt5.QtGui.QIcon(':/icon/assistanter.png'))
        self.double_column = double_column
        if self.double_column:
            column_num = 1 + (len(self.selection_list) + 1 ) // 2
        else:
            column_num = len(self.selection_list)
        self.setFixedSize(300, column_num * 40)
        self.selection = None
        self.initGui()
        self.createLayout()
        #self.btn_ok.pressed.connect(self.setSelection)

    def initGui(self):
        #self.btn_ok = PyQt5.QtWidgets.QPushButton('OK')
        self.createGroupBox()

    def createGroupBox(self):
        self.radio_list = []
        for s in self.selection_list:
            radio = PyQt5.QtWidgets.QRadioButton(s)
            self.radio_list.append(radio)
            radio.clicked.connect(self.setSelection)
        self.group_box = PyQt5.QtWidgets.QGroupBox(self.title + ' Selection')
        #self.radio_list[0].setChecked(True)
        self.radio_layout = PyQt5.QtWidgets.QGridLayout()
        for i in range(len(self.radio_list)):
            if self.double_column:
                self.radio_layout.addWidget(self.radio_list[i], i // 2, i % 2, 1, 1)
            else:
                self.radio_layout.addWidget(self.radio_list[i], i, 0, 1, 1)
        self.group_box.setLayout(self.radio_layout)

    def createLayout(self):
        self.layout = PyQt5.QtWidgets.QGridLayout()
        self.layout.addWidget(self.group_box, 0, 0, 2, 4)
        #self.layout.addWidget(self.btn_ok, 5, 3, 1, 1)
        self.setLayout(self.layout)

    def setSelection(self):
        for radio in self.radio_list:
            if radio.isChecked():
                self.selection = radio.text()
                break
        time.sleep(0.3)
        self.close()


class CTextInput(PyQt5.QtWidgets.QDialog):
    def __init__(self):
        super(CTextInput, self).__init__()
        self.setWindowTitle('Text Input')
        self.setWindowIcon(PyQt5.QtGui.QIcon(':/icon/assistanter.png'))
        self.setFixedSize(300,100)
        self.input_text = None
        self.initGui()
        self.createLayout()
        self.btn_ok.pressed.connect(self.setInputText)

    def initGui(self):
        self.label = PyQt5.QtWidgets.QLabel('Content :')
        self.input = PyQt5.QtWidgets.QLineEdit()
        self.btn_ok = PyQt5.QtWidgets.QPushButton('OK')

    def createLayout(self):
        self.layout = PyQt5.QtWidgets.QGridLayout()
        self.layout.addWidget(self.label, 1,0,1,1)
        self.layout.addWidget(self.input, 1,1,1,4)
        self.layout.addWidget(self.btn_ok, 2,2,1,1)
        self.setLayout(self.layout)

    def setInputText(self):
        self.input_text = self.input.text()
        self.close()


class CAssistanter(CDefaultWindow):
    assistantCoding = PyQt5.QtCore.pyqtSignal(str)
    touchSignal = PyQt5.QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(CAssistanter, self).__init__()
        self.setWindowTitle('Assistanter')
        self.setWindowIcon(PyQt5.QtGui.QIcon(':/icon/assistanter.png'))
        self.parent = parent
        self.msg_painter_queue = Queue()
        self.capture_msg_queue = Queue()
        self.button_dict = {}
        self.btn_font = PyQt5.QtGui.QFont("微软雅黑",10)
        self.initGui()
        self.createLayout()
#        self.resize(180, self.height())
#        self.setFixedWidth(180)
        self.setFeatures(PyQt5.QtWidgets.QDockWidget.DockWidgetClosable)
        word_width = PyQt5.QtGui.QFontMetrics(self.btn_font).width('a')
        word_len = max([len(w) for w in self.action_list]) + 6
        self.setFixedWidth(word_width*word_len)

    def createButton(self, icon='', text='', name='button', style_sheet=None):
        icon = ':/icon/%s' % icon
        tip = self.getButtonTip(text)
        text = ' ' + text
        button = PyQt5.QtWidgets.QPushButton(PyQt5.QtGui.QIcon(icon), text)
        button.setFixedHeight(35)
        if style_sheet:
            button.setStyleSheet(style_sheet)
        self.button_dict[name] = button
        button.setFont(self.btn_font)
        button.setIconSize(PyQt5.QtCore.QSize(24,24))
        button.setToolTip(tip)
        if text == ' Tbox':
            button.pressed.connect(self.showTboxCommand)
        elif text == ' play_file':
            button.pressed.connect(self.play_file)
        elif text == ' start_record':
            button.pressed.connect(self.start_record)
        elif text == ' match_record':
            button.pressed.connect(self.match_record)
        elif text == ' stop_record':
            button.pressed.connect(self.stop_record)            
        else:
            button.pressed.connect(self.autoCoding)

    def initGui(self):
        self.widget = PyQt5.QtWidgets.QWidget()
        self.widget.move(PyQt5.QtCore.QPoint(0,5))
        self.widget.setContentsMargins(0,0,0,0)
        self.scrollArea = PyQt5.QtWidgets.QScrollArea(self)
        self.scrollArea.setHorizontalScrollBarPolicy(PyQt5.QtCore.Qt.ScrollBarAlwaysOff)
        self.action_list = ['Tbox', 'keyevent', 'touch', 'touch_if', 'touch_in', 'touch_or',
                            'long_touch', 'sleep', 'text', 'snapshot', 'swipe','flick', 'pinch',
                            'exists','assert_exists', 'assert_not_exists', 'start_record',
                            'play_file', 'stop_record', 'match_record']
        icon_list = ['', 'keyevent.png', 'touch.png','touch.png','touch.png',
                     'touch.png','touch.png', 'sleep.png', 'text.png','snapshot.png','swipe.png',
                     'flick.png', 'pinch.png','','', '', 'touch.png', 'touch.png', 'touch.png', 'touch.png']
        style_sheet = '''
                        QPushButton{background-color:rgb(100,100,100);
                                    color: white;
                                    text-align: left;
                                    border-radius: 10px; 
                                    border: 2px groove gray;
                                    border-style: outset;}

                        QPushButton:hover{border-radius: 10px;
                                        border:2px rgb(0, 255, 255);
                                        border-style: outset;}

                        QPushButton:pressed{background-color:rgb(240,240,240);}
        '''
        for i in range(len(self.action_list)):
            try:
                icon = icon_list[i]
            except:
                icon = ''
            if icon == '':
                icon = 'default.png'
            self.createButton(icon, self.action_list[i], self.action_list[i], style_sheet)

    def createLayout(self):
        self.layout = PyQt5.QtWidgets.QVBoxLayout()
        for button_name in self.action_list:
            self.layout.addWidget(self.button_dict[button_name])
        self.widget.setLayout(self.layout)
        self.scrollArea.setWidget(self.widget)
        self.setWidget(self.scrollArea)

    def resizeEvent(self, event):
        self.widget.setFixedWidth(self.width())
        for button in self.button_dict.values():
            w = min(int(self.width()*0.9), self.width() - 35)
            button.setFixedWidth(w)

    def getButtonTip(self, string):
        if string == 'Tbox':
            return 'Tbox commands...'
        params = eval('signature(%s)' % string)
        doc = eval('%s.__doc__' % string)
        tips = string + str(params)
        if doc:
            tips += '\n' + doc
        return tips

    def question(self, quesion_str):
        reply = PyQt5.QtWidgets.QMessageBox.question(self, 'Message',
                                                    quesion_str,
                                                    PyQt5.QtWidgets.QMessageBox.Yes,
                                                    PyQt5.QtWidgets.QMessageBox.No)
        if reply == PyQt5.QtWidgets.QMessageBox.Yes:
            return True
        else:
            return False

    def message(self, msg):
        PyQt5.QtWidgets.QMessageBox.information(self,
                                                'Assistanter',
                                                msg,
                                                PyQt5.QtWidgets.QMessageBox.Ok)

    def insertImage(self, filename):
        if not filename:
            return
        name = filename.replace('/', os.sep).split(os.sep)[-1]
        if not self.parent:
            return
        try:
            editor = self.parent.editor.currentWidget()
            if editor:
                try:
                    string = "Template('%s')" % name
                    editor.scintilla.insert(string)
                    x, y = editor.scintilla.getCursorPosition()
                    editor.scintilla.setCursorPosition(x, y + len(string))
                    editor.scintilla.setFocus()
                except:
                    editor.insertImage(filename)
                    editor.setFocus()
        except:
            import traceback
            print(traceback.print_exc())

    def insertText(self, string):
        if self.parent:
            try:
                editor = self.parent.editor.currentWidget()
                if editor:
                    try:
                        editor.scintilla.insert(string)
                        x, y = editor.scintilla.getCursorPosition()
                        editor.scintilla.setCursorPosition(x, y + len(string))
                        editor.scintilla.setFocus()
                    except:
                        editor.insertPlainText(string)
                        editor.setFocus()
            except:
                import traceback
                print(traceback.print_exc())

    def getCurrentEditorCaseDir(self):
        index = self.parent.editor.currentIndex()
        if index > -1:
            filename = self.parent.editor.tabToolTip(index)
            case_dir = os.sep.join(filename.split('/')[:-1])
        else:
            case_dir = None
        return case_dir

    def showAssistanter(self):
        if self.parent:
            splitter_center_lenght = sum(self.parent.splitter_center.sizes())
            splitter_main_length = sum(self.parent.splitter_main.sizes())
            if not self.isVisible():
                self.parent.splitter_main.moveSplitter(splitter_main_length * 0.1, 1)
                self.parent.splitter_center.moveSplitter(splitter_center_lenght * 0.8, 1)
                self.show()
            else:
                self.close()

    def closeEvent(self, event):
        if self.parent:
            splitter_center_lenght = sum(self.parent.splitter_center.sizes())
            splitter_main_length = sum(self.parent.splitter_main.sizes())
            self.parent.splitter_main.moveSplitter(splitter_main_length * 0.2, 1)
            self.parent.splitter_center.moveSplitter(splitter_center_lenght * 0.618, 1)

    def capture(self):
        if self.parent:
            self.parent.captureWindow.capture_file = None
            self.parent.captureWindow.screen.assistant_flag = True
            self.parent.screenCapture(auto_naming=True)
            self.parent.captureWindow.screen.assistant_flag = False
            return self.parent.captureWindow.capture_file
        return None

    def getSelectionPosition(self, button):
        w, h = button.width(), button.height()
        p = button.mapToGlobal(PyQt5.QtCore.QPoint(w-1, 0))
        return p

    def autoCoding(self):
        for button in self.button_dict.values():
            if button.isDown():
                break
        self.button_position = self.getSelectionPosition(button)
        text = button.text().strip()
        paras = self.getParas(self.getApiParas(text))
        paras_list = [p[1] for p in paras]
        if None in paras_list or '' in paras_list:
            return
        self.insertText(text + '(')
        if len(paras) == 0:
            self.insertText(self.getDefaultParas(text))
        else:
            for i in range(len(paras)):
                pic_flag, para = paras[i]
                if pic_flag:
                    self.insertImage(para)
                else:
                    self.insertText(para)
                if i < len(paras) -1:
                    self.insertText(',')
        if text in ['touch',
                    'touch_if',
                    'touch_in',
                    'touch_or',
                    'long_touch',
                    'swipe',
                    'flick',
                    'pinch',
                    'text',
                    'keyevent',
                    'snapshot',
                    'exists',
                    'assert_exists',
                    'assert_not_exists'
                    ]:
            if REC.DEVICE_NUM > 1 and REC.DEVICE_URI:
                self.insertText(", device=%s" % REC.DEVICE_URI_MAPPING.get(REC.DEVICE_URI))
        self.insertText(')' + os.linesep)
        try:
            self.parent.editor.currentWidget().moveScrollToEnd()
        except:
            pass

    def getApiParas(self, text):
        """
        The meaning of para type is list as below:
            0: picture
            1: text
            2: keyevent
            3: direction
            4: special case (pinch)
            5: file path
            6: nothing

            eg: 'touch':[0],
                this meaning is touch api need one parameter, the type of parameter is picture
        """
        paras_mapping = {'touch': [0],
                       'touch_if': [0],
                       'touch_in': [0, 0],
                       'touch_or': [0, 0],
                       'long_touch': [0],
                       'swipe': [0, 0],
                       'flick': [0, 3],
                       'pinch': [0, 4],
                       'sleep': [],
                       'text': [1],
                       'keyevent': [2],
                       'snapshot': [],
                       'exists': [0],
                       'assert_exists': [0],
                       'assert_not_exists': [0],
                       'being_record':[6],
                       'play_file' : [6],
                       'end_record' : [6],
                        }
        api_paras = paras_mapping.get(text)
        return api_paras

    def getParas(self, paras_type_list):  ##paras_type_list   0: picture  1:text
        paras_result = []
        pic_count = paras_type_list.count(0)
        capture_msg = []
        msg = 'Please capture %s target picture in device window...'
        if pic_count == 1:
            capture_msg.append(msg % 'the')
        elif pic_count == 2:
            capture_msg.append(msg % 'the')
            capture_msg.append(msg % 'another')
        else:
            pass
        self.capture_msg_queue = Queue()
        for msg in capture_msg:
            self.capture_msg_queue.put(msg)
        for paras_type in paras_type_list:
            if paras_type == 0:
                paras = self.getCapture()
            elif paras_type == 1:
                paras = self.getText()
            elif paras_type == 2:
                paras = self.getKeyevent()
            elif paras_type == 3:
                paras = self.getDirection()
            elif paras_type == 4:
                paras = [False, 'scale=0.5']
            elif paras_type == 5:
                paras = self.getFilePath()                              
            else:                
                paras = [None, None]
#            if paras_type in (0, 1, 2, 3):
            paras_result.append(paras)
            time.sleep(0.3)
            try:
                if not paras[1]:
                    break
            except:
                pass
        return paras_result

    def getDefaultParas(self, text):
        default_paras = {'snapshot': '',
                         'sleep': '1.0'
                         }
        return default_paras.get(text)

    def getCapture(self):
        if not self.capture_msg_queue.empty():
            msg = self.capture_msg_queue.get()
        self.setMsg(msg)
        capture_file = self.capture()
        if not capture_file:
            self.current_msg_painter_flag[0] = False
        return [True, capture_file]

    def getText(self):
        t = CTextInput()
        t.exec_()
        input_text = t.input_text
        if input_text is not None:
            input_text = "'%s'" % input_text
        return [False, input_text]

    def getCaseDir(self):
            
        dirname = PyQt5.QtWidgets.QFileDialog.getExistingDirectory(self, 'Set Directory',
                                                                   '',
                                                                   PyQt5.QtWidgets.QFileDialog.ShowDirsOnly)
        #dirname = dirname.replace('/', os.sep)
        return dirname
    
    def getFilePath(self):

        filename, _ = PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,
                                                                  'Open audio file',
                                                                   "", "audio(*.wav)")  
        filename = filename.split('/')[-1]      
        return filename
    def getKeyevent(self):
        keyevent_list = ['HOME', 'SEEK', 'MENU', 'TRACK','AUDIO','PHONE',
                         'MAP','APPS', 'VOLUME_UP','TUNE_UP', 'VOLUME_DOWN',
                         'TUNE_DOWN', 'VOICE']
        k = CSelection('Keyevent', keyevent_list, True)
        k.move(self.button_position)
        k.exec_()
        return [False, k.selection]

    def getDirection(self):
        direction_list = ['DIR_UP', 'DIR_DOWN', 'DIR_LEFT', 'DIR_RIGHT',
                          'DIR_UP_LEFT', 'DIR_UP_RIGHT', 'DIR_DOWN_LEFT', 'DIR_DOWN_RIGHT']
        d = CSelection('Direction', direction_list)
        d.move(self.button_position)
        d.exec_()
        return [False, d.selection]

    def showMsg(self, msg):
        return
        m = assistanterMsg.CMsg(msg=msg)
        m.showMsg()

    def setMsg(self, msg):
        self.current_msg_painter_flag = [True]
        self.msg_painter_queue.put(self.current_msg_painter_flag)
        self.parent.captureWindow.msg = msg
        self.parent.captureWindow.screen.repaint()
        import threading
        t = threading.Thread(target=self.clearMsg, args=(3.0,))
        t.start()

    def clearMsg(self, t):
        time.sleep(t)
        msg_painter_flag = True
        if not self.msg_painter_queue.empty():
            msg_painter_flag = self.msg_painter_queue.get()[0]
        if msg_painter_flag:
            self.parent.captureWindow.msg = ''
            self.parent.captureWindow.screen.repaint()

    def showTboxCommand(self):
        tbox = tboxCommand.CTboxCommand(self)
        tbox_position = self.getSelectionPosition(self.button_dict['Tbox'])
        tbox.move(tbox_position)
        tbox.exec_()

    def play_file(self):
        filename = self.getFilePath()
        self.insertText("play_file('" + filename + "')\n")
        ##case_dir = self.parent.getCaseDir()
        ##filename = filename.replace('/', os.sep)
        # case_list = play_wave_file(filename)
        # for i in range(len(case_list)):
        #     self.insertText(case_list[i])

    def start_record(self):
        case_dir = self.getCaseDir()
        self.insertText("start_audio_test('" + case_dir + "')\n")
        # case_list = start_record(case_dir)
        # for i in range(len(case_list)):
        #     self.insertText(case_list[i])

    def stop_record(self):
        self.insertText("stop_audio_test()\n")
        # case_list = stop_record()
        # for i in range(len(case_list)):
        #     self.insertText(case_list[i])

    def match_record(self):
        filename = self.getFilePath()
        self.insertText("match_microphone('" + filename + "')\n")
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = CAssistanter()
    w.show()
    sys.exit(app.exec_())   