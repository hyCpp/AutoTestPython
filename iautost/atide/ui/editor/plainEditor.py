# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-7-19

@author: wushengbing
'''
import sys
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.Qsci import * 
from ui.editor.lexer.syntax_highlight_color import highlightColor2
from ui.editor.lexer.lexer_python import CLexerPython  


class CPlainEditor(QWidget):
    toolbarUpdate = pyqtSignal()

    def __init__(self, font, parent=None):
        self.parent = parent
        self.change_times = -1
        super(CPlainEditor, self).__init__(parent)
        self.__setFont(font)
        self.__initScintilla()
        self.__createLayout()
        self.scintilla.textChanged.connect(self.textChanged)
        self.scintilla.linesChanged.connect(self.linesChanged)
        self.setWindowFlags(Qt.FramelessWindowHint)

    def linesChanged(self):
        self.scintilla.setMarginWidth(0, self.fontmetrics.width(str(self.scintilla.lines())) + 5)
    
    def textChanged(self):
        self.change_times += 1
        self.toolbarUpdate.emit()

    def __createLayout(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.addWidget(self.scintilla)
        self.setLayout(self.layout)

    def __setFont(self, font):
        self.font = font
        self.setFont(self.font)
        self.fontmetrics = QFontMetrics(self.font)
  
    def __initScintilla(self):
        self.scintilla = QsciScintilla()
        self.scintilla.setUtf8(True)
        self.scintilla.setFont(self.font)
        self.scintilla.setMarginsFont(self.font)
        
        self.scintilla.setWrapMode(QsciScintilla.WrapNone)
  
        #set line number width
        self.scintilla.setMarginWidth(0, self.fontmetrics.width(str(self.scintilla.lines())) + 5)
        self.scintilla.setMarginLineNumbers(0, True)
  
        #mesure line  
        self.scintilla.setEdgeMode(QsciScintilla.EdgeLine)
        self.scintilla.setEdgeColumn(150)
        self.scintilla.setEdgeColor(QColor("#BBB8B5"))
  
        #brace match
        self.scintilla.setBraceMatching(QsciScintilla.StrictBraceMatch)
  
        #current line color
        self.scintilla.setCaretLineVisible(True)
        self.scintilla.setCaretLineBackgroundColor(QColor(highlightColor2['CurrentLine']))
        self.scintilla.setCaretForegroundColor(QColor("green"))
  
        #selection color
        self.scintilla.setSelectionBackgroundColor(QColor("#3399FF"))
        self.scintilla.setSelectionForegroundColor(QColor("#FFFFFF"))
  
        #table relative  
        self.scintilla.setIndentationsUseTabs(False)
        self.scintilla.setIndentationWidth(4)
        self.scintilla.setTabIndents(True)
        self.scintilla.setAutoIndent(True)
        self.scintilla.setBackspaceUnindents(True)
        self.scintilla.setTabWidth(4)
  
        #indentation guides  
        self.scintilla.setIndentationGuides(True)
  
        #line number margin color  
        self.scintilla.setMarginsBackgroundColor(QColor("#AAEEB3")) #272727
        self.scintilla.setMarginsForegroundColor(QColor("7F7F7F"))
  
        #folding margin  
        self.scintilla.setFolding(QsciScintilla.PlainFoldStyle)
        self.scintilla.setMarginWidth(2,12)
        #marker  
        self.scintilla.markerDefine(QsciScintilla.Minus,QsciScintilla.SC_MARKNUM_FOLDEROPEN)
        self.scintilla.markerDefine(QsciScintilla.SC_MARK_BOXPLUS,QsciScintilla.SC_MARKNUM_FOLDER)
        self.scintilla.markerDefine(QsciScintilla.Minus,QsciScintilla.SC_MARKNUM_FOLDEROPENMID)
        self.scintilla.markerDefine(QsciScintilla.Plus,QsciScintilla.SC_MARKNUM_FOLDEREND)
        
#        self.scintilla.markerDefine(QsciScintilla.Circle,QsciScintilla.SC_STATUS_FAILURE)
#        self.scintilla.markerDefine(QsciScintilla.Circle,QsciScintilla.SC_STATUS_BADALLOC)
#        self.scintilla.markerDefine(QsciScintilla.Circle,QsciScintilla.SC_STATUS_WARN_START)
#        self.scintilla.markerDefine(QsciScintilla.SC_STATUS_FAILURE, QsciScintilla.SC_MOD_LEXERSTATE)

        #marker define color  
        self.scintilla.setMarkerBackgroundColor(QColor("#FFFFFF"),QsciScintilla.SC_MARKNUM_FOLDEREND)
        self.scintilla.setMarkerForegroundColor(QColor("#EA0EB4"),QsciScintilla.SC_MARKNUM_FOLDEREND)
        self.scintilla.setMarkerBackgroundColor(QColor("#FFFFFF"),QsciScintilla.SC_MARKNUM_FOLDEROPENMID)
        self.scintilla.setMarkerForegroundColor(QColor("#EA0EB4"),QsciScintilla.SC_MARKNUM_FOLDEROPENMID)
        self.scintilla.setMarkerBackgroundColor(QColor("#FFFFFF"),QsciScintilla.SC_MARKNUM_FOLDER)
        self.scintilla.setMarkerForegroundColor(QColor("#EA0EB4"),QsciScintilla.SC_MARKNUM_FOLDER)
        self.scintilla.setMarkerBackgroundColor(QColor("#FFFFFF"),QsciScintilla.SC_MARKNUM_FOLDEROPEN)
        self.scintilla.setMarkerForegroundColor(QColor("#EA0EB4"),QsciScintilla.SC_MARKNUM_FOLDEROPEN) #272727
        self.scintilla.setFoldMarginColors(QColor("#7F7F7F"),QColor("#7F7F7F"))
        #  highlightColor2['FoldMargin']
        #whitespace  
        self.scintilla.setWhitespaceVisibility(QsciScintilla.WsInvisible)
        self.scintilla.setWhitespaceSize(2)
        self.scintilla.setMarginWidth(1,0)
  
        #set lexer  
        self.lexer = CLexerPython()
        self.lexer.setFont(self.font)
        self.scintilla.setLexer(self.lexer)
        
        #set typing complete
        self.apis = QsciAPIs(self.lexer)
        self.apis.load('ui/editor/lexer/complete.txt')
        self.apis.prepare()
        self.scintilla.setAutoCompletionSource(QsciScintilla.AcsAll)
        self.scintilla.setAutoCompletionCaseSensitivity(True)
        self.scintilla.setAutoCompletionThreshold(1)

        #set bold font
        self.font.setBold(True)
        for name in [CLexerPython.ClassName, 
                     CLexerPython.FunctionMethodName, CLexerPython.Number]:
            self.lexer.setFont(self.font, name)
        self.font.setBold(False)
        
        #set highlight
        self.lexer.setColor(QColor(highlightColor2['Default']))
#        self.lexer.setPaper(QColor(highlightColor2['Paper']))
        self.lexer.setColor(QColor(highlightColor2['ClassName']),CLexerPython.ClassName)
        self.lexer.setColor(QColor(highlightColor2['Keyword']),CLexerPython.Keyword)
        self.lexer.setColor(QColor(highlightColor2['Comment']),CLexerPython.Comment)
        self.lexer.setColor(QColor(highlightColor2['Number']),CLexerPython.Number)
        self.lexer.setColor(QColor(highlightColor2['String']),CLexerPython.SingleQuotedString)
        self.lexer.setColor(QColor(highlightColor2['String']),CLexerPython.DoubleQuotedString)
        self.lexer.setColor(QColor(highlightColor2['String']),CLexerPython.TripleSingleQuotedString)
        self.lexer.setColor(QColor(highlightColor2['String']),CLexerPython.TripleDoubleQuotedString)
        self.lexer.setColor(QColor(highlightColor2['FunctionMethodName']),CLexerPython.FunctionMethodName)
        self.lexer.setColor(QColor(highlightColor2['Operator']),CLexerPython.Operator)
        self.lexer.setColor(QColor(highlightColor2['Identifier']),CLexerPython.Identifier)
        self.lexer.setColor(QColor(highlightColor2['CommentBlock']),CLexerPython.CommentBlock)
        self.lexer.setColor(QColor(highlightColor2['UnclosedString']),CLexerPython.UnclosedString)
        self.lexer.setColor(QColor(highlightColor2['HighlightedIdentifier']),CLexerPython.HighlightedIdentifier)
        self.lexer.setColor(QColor(highlightColor2['Decorator']),CLexerPython.Decorator)
        
        