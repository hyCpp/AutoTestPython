# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-7-19

@author: wushengbing
'''
import sys
import os
import re
from PIL import Image
from bs4 import BeautifulSoup
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from ui.editor.lexer.syntax_highlight_color import highlightColor2
from ui.common.traceback import trace


class CLineNumberArea(QWidget):

    def __init__(self, editor):
        super(CLineNumberArea, self).__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class CRichEditor(QTextEdit):
    toolbarUpdate = pyqtSignal()

    def __init__(self, font, parent=None):
        super(CRichEditor, self).__init__(parent)
        self.parent = parent
        self.change_times = -1
        self.__setFont(font)
        self.textChanged.connect(self.changed)
        self.setWordWrapMode(QTextOption.WordWrap)
        self.setLineWrapMode(QTextEdit.NoWrap)

        ##line number
        self.lineNumberArea = CLineNumberArea(self)
        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.lineNumberScrollArea = QScrollArea(self)
        self.lineNumberScrollArea.setWidget(self.lineNumberArea)
        self.lineNumberScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lineNumberScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalScrollBar().rangeChanged.connect(self.lineNumberScrollArea.verticalScrollBar().setRange)
        self.textChanged.connect(self.lineNumberArea.update)
        self.verticalScrollBar().valueChanged.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

        #completer
        self.completer = None
        self.word_list = []
        completer = QCompleter(self)
        completer.setModel(self.modelFromFile(self));
        completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setWrapAround(False)
        self.setCompleter(completer)
        self.img_ratio = 1

    def __setFont(self, font):
        self.font = font
        self.setFont(self.font)
        self.fontmetrics = QFontMetrics(self.font)

    def event(self, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText("    ")
            return True
        return QTextEdit.event(self, event)

    def insertImage(self, image):
        img_width, img_height = Image.open(image).size
        img_width = int(img_width * self.img_ratio)
        img_height = int(img_height * self.img_ratio)
        cursor = self.textCursor()
        cursor.insertHtml("<img src='%s' width='%s' height='%s'/>" % (image, img_width, img_height))

    def changed(self):
        self.change_times += 1
        self.toolbarUpdate.emit()
#        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().maximum())

    def moveScrollToEnd(self):
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().maximum())

    @trace
    def lineNumberAreaWidth(self):
        document = self.document()
        block_count = document.blockCount()
        line_count = max(10, block_count)
        width = 4 + QFontMetrics(self.font).width('9') * len(str(line_count))
        return width

    @trace
    def updateLineNumberAreaWidth(self, newBlockCount):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)  ## left, top, right, bottom

    @trace
    def updateLineNumberArea(self, dy):
        self.lineNumberScrollArea.verticalScrollBar().setValue(dy)

    @trace
    def resizeEvent(self, event):
        QTextEdit.resizeEvent(self, event)
        rect = self.contentsRect()
        new_rect = QRect(rect.left(),
                         rect.top(),
                         self.lineNumberAreaWidth(),
                         rect.height())
        self.lineNumberArea.setGeometry(new_rect)
        self.lineNumberScrollArea.setGeometry(new_rect)

    def updateNumberAreaHeight(self, block):
        height = 100
        while(block.isValid()):
            height += QPlainTextEdit().blockBoundingRect(block).height()
            block = block.next()
        height = max(height, self.lineNumberArea.height(), self.height())
        self.lineNumberArea.setFixedHeight(height)

    @trace
    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), Qt.lightGray)
        document = self.document()
        self.updateNumberAreaHeight(document.firstBlock())
        block = document.firstBlock()
        block_number = block.blockNumber()
        top = QPlainTextEdit().blockBoundingGeometry(block).\
                    translated(QPlainTextEdit().contentOffset()).top()
        bottom = top + QPlainTextEdit().blockBoundingRect(block).height()
        while (block.isValid() and top <= event.rect().bottom()):
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top,
                                 self.lineNumberArea.width(),
                                 QFontMetrics(self.font).height(),
                                 Qt.AlignCenter, number)
                                    #Qt.AlignCenter, Qt.AlignRight
            block = block.next()
            top = bottom
            bottom = top + QPlainTextEdit().blockBoundingRect(block).height()
            block_number += 1
#            block_number = block.blockNumber()

    def highlightCurrentLine(self):
        line_color = QColor(highlightColor2['CurrentLine'])
        all_selection = []
        selection = self.ExtraSelection()
        selection.format.setBackground(line_color)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        all_selection.append(selection)
        self.setExtraSelections(all_selection)

    def setCompleter(self, QComp_obj):
        self.completer = QComp_obj
        if not self.completer:
            return
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insertCompletion)

    def completer(self):
        return self.completer

    @trace
    def insertCompletion(self, completion):  #QString
        if self.completer.widget() != self:
            return
        textCursor = self.textCursor()
        prefix = len(self.completer.completionPrefix())
        textCursor.movePosition(QTextCursor.Left)
        textCursor.movePosition(QTextCursor.EndOfWord)
        textCursor.insertText(completion[prefix:])
        self.setTextCursor(textCursor)

    def textUnderCursor(self):
        textCursor = self.textCursor()
        textCursor.select(QTextCursor.WordUnderCursor)
        return textCursor.selectedText()

    @trace
    def modelFromFile(self, parent, filename='ui/editor/lexer/complete.txt'):
        try:
            with open(filename, 'r') as f:
                word_list = f.readlines()
        except:
            word_list = []
        for w in word_list:
            if not w.startswith('#'):
                w = w.strip()
                if w not in self.word_list:
                    self.word_list.append(w)
        return QStringListModel(self.word_list, parent)

    @trace
    def focusInEvent(self, event):
        if self.completer:
            self.completer.setWidget(self)
        QTextEdit.focusInEvent(self, event)

    @trace
    def keyPressEvent(self, event):
        if self.completer and self.completer.popup().isVisible():
            if event.key() in [Qt.Key_Enter, Qt.Key_Return,
                               Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab]:
                event.ignore()
                return
        QTextEdit.keyPressEvent(self, event)
        if event.modifiers() and (Qt.ControlModifier or Qt.ShiftModifier):
            ctrl_shift = True
        else:
            ctrl_shift = False
        if not self.completer or ctrl_shift and event.text() in ['', None]:
            return

        word_end = "~!@#$%^&*()+{}|:\"<>?,./;'[]\\-="

        if (event.modifiers() != Qt.NoModifier) and not ctrl_shift:
            has_modifier = True
        else:
            has_modifier = False
        completionPrefix = self.textUnderCursor()

        if (has_modifier or event.text() in ['', None] \
                                            or len(completionPrefix) < 1
                                            or word_end.find(event.text()[-1]) != -1):
            self.completer.popup().hide()
            return

        if completionPrefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completionPrefix)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0,0))

        rect = self.cursorRect(self.textCursor())
        rect.setWidth(self.completer.popup().sizeHintForColumn(0) \
                      + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(rect)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            step = 0.05
        else:
            step = -0.05
        if self.parent.ctrl_alt_flag == 2:
            self.img_ratio += step
            if self.img_ratio > 2:
                self.img_ratio = 2
            if self.img_ratio < 0.1:
                self.img_ratio = 0.1
            self.imageSizeAdjust()
        else:
            value = self.verticalScrollBar().value() - step * 200
            self.verticalScrollBar().setValue(value)

    def imageSizeAdjust(self):
        html_string = self.toHtml()
        html=BeautifulSoup(html_string,'html.parser') ###html.parser  lxml
        for img_tag in html.find_all('img', src=True):
            img_path = img_tag['src']
            img_width, img_height = Image.open(img_path).size
            if self.img_ratio in (0.1, 2):
                try:
                    if int(img_tag['width']) == int(img_width * 0.1) \
                        or int(img_tag['width']) == int(img_width * 2):
                        return
                except:
                    pass
            img_tag['width'] = "%s" % int(img_width * self.img_ratio)
            img_tag['height'] = "%s" % int(img_height * self.img_ratio)
        html_string = str(html)
#        self.clear()
        self.setHtml(html_string)
        self.parent.statusBarMessageShow.emit('image size : {}%'.format(round(self.img_ratio*100)))

