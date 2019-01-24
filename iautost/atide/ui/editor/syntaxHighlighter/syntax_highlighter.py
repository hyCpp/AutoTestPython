# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-5-28

@author: wushengbing
'''

import os
import sys
from PyQt5.QtCore import QEvent, QFile, \
        QFileInfo, QIODevice, QRegExp, QTextStream, Qt
from PyQt5.QtWidgets import QAction, QApplication, \
        QFileDialog, QMainWindow, QMessageBox, QTextEdit
from PyQt5.QtGui import QFont, QIcon, QColor, QKeySequence, \
         QSyntaxHighlighter, QTextCharFormat, QTextCursor


COLOR_STYLE = [ ("normal", Qt.black),
                ("keyword", Qt.darkBlue), 
                ("builtin", Qt.darkRed),
                ("constant", Qt.darkGreen),
                ("decorator", Qt.darkBlue),
                ("comment", Qt.darkGreen),
                ("string", Qt.darkYellow), 
                ("number", Qt.darkMagenta),
                ("error", Qt.darkRed)
            ]

#eclipse
COLOR_STYLE2 = [("normal", Qt.black),
                ("keyword", 0x0000FF),
                ("comment", 0x800000),                
                ("string", 0x00AA00),                
                ("decorator", 0x7D7D7D),
                ("number", 0x800000),
                ("self", 0xFF06FF),
                ("builtin", 0x9919DC),
                ("constant", 0x0000FF),
                ("class_func_name", Qt.black),            
                ("error", Qt.darkRed),
                ("python_p", 0xFF06FF),
                ("brackets", Qt.black)
            ]



class PythonHighlighter(QSyntaxHighlighter):

    Rules = []
    Formats = {}

    def __init__(self, parent=None):
        super(PythonHighlighter, self).__init__(parent)

        self.initializeFormats()

        KEYWORDS = ["and", "as", "assert", "break", "class",
                "continue", "def", "del", "elif", "else", "except",
                "exec", "finally", "for", "from", "global", "if",
                "import", "in", "is", "lambda", "not", "or", "pass",
                "print", "raise", "return", "try", "while", "with",
                "yield"]
        BUILTINS = ["abs", "all", "any", "basestring", "bool",
                "callable", "chr", "classmethod", "cmp", "compile",
                "complex", "delattr", "dict", "dir", "divmod",
                "enumerate", "eval", "execfile", "exit", "file",
                "filter", "float", "frozenset", "getattr", "globals",
                "hasattr", "hex", "id", "int", "isinstance",
                "issubclass", "iter", "len", "list", "locals", "map",
                "max", "min", "object", "oct", "open", "ord", "pow",
                "property", "range", "reduce", "repr", "reversed",
                "round", "set", "setattr", "slice", "sorted",
                "staticmethod", "str", "sum", "super", "tuple", "type",
                "vars", "zip"] 
        CONSTANTS = ["False", "True", "None", "NotImplemented",
                     "Ellipsis"]

        PythonHighlighter.Rules.append((QRegExp(r"\bself\b"), "self"))
        class_func_regExp = r"\bdef +\w+\({1}|\bclass +\w+\({1}|\bclass +\w+:{1}"
        PythonHighlighter.Rules.append((QRegExp(class_func_regExp), "class_func_name"))
        PythonHighlighter.Rules.append((QRegExp(r"\("), "brackets"))
        PythonHighlighter.Rules.append((QRegExp(r"\b__\w+__\b"), "python_p"))
#        PythonHighlighter.Rules.append((QRegExp(r"#.*"), "comment"))
        PythonHighlighter.Rules.append((QRegExp(
                "|".join([r"\b%s\b" % keyword for keyword in KEYWORDS])),
                "keyword"))
        PythonHighlighter.Rules.append((QRegExp(
                "|".join([r"\b%s\b" % builtin for builtin in BUILTINS])),
                "builtin"))
        PythonHighlighter.Rules.append((QRegExp(
                "|".join([r"\b%s\b" % constant
                for constant in CONSTANTS])), "constant"))
        PythonHighlighter.Rules.append((QRegExp(
                r"\b[+-]?[0-9]+[lL]?\b"
                r"|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b"
                r"|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"),
                "number"))
        PythonHighlighter.Rules.append((QRegExp(r"\b@\w+\b"),
                "decorator"))
        stringRe = QRegExp(r"""(?:'[^']*'|"[^"]*")""")
        stringRe.setMinimal(True)
        PythonHighlighter.Rules.append((stringRe, "string"))
        self.stringRe = QRegExp(r"""(:?"["]".*"["]"|'''.*''')""")
        self.stringRe.setMinimal(True)
        PythonHighlighter.Rules.append((self.stringRe, "string"))
        self.tripleSingleRe = QRegExp(r"""'''(?!")""")
        self.tripleDoubleRe = QRegExp(r'''"""(?!')''')
        PythonHighlighter.Rules.append((QRegExp(r"#.*"), "comment"))
        
    @staticmethod
    def initializeFormats():
        baseFormat = QTextCharFormat()
        baseFormat.setFontFamily("courier")
        baseFormat.setFontPointSize(12)
        for name, color in COLOR_STYLE2:
            format = QTextCharFormat(baseFormat)
            format.setForeground(QColor(color))
            if name in ("keyword", "decorator", "number","class_func_name"):
                format.setFontWeight(QFont.Bold)
#            if name == "comment":
#                format.setFontItalic(True)
            PythonHighlighter.Formats[name] = format

    def highlightBlock(self, text):
        NORMAL, TRIPLESINGLE, TRIPLEDOUBLE, ERROR = range(4)
        textLength = len(text)
        prevState = self.previousBlockState()

        self.setFormat(0, textLength,
                       PythonHighlighter.Formats["normal"])

        if text.startswith("Traceback") or text.startswith("Error: "):
            self.setCurrentBlockState(ERROR)
            self.setFormat(0, textLength,
                           PythonHighlighter.Formats["error"])
            return
        if (prevState == ERROR and
            not (text.startswith(sys.ps1) or text.startswith("#"))):
            self.setCurrentBlockState(ERROR)
            self.setFormat(0, textLength,
                           PythonHighlighter.Formats["error"])
            return

        for regex, format in PythonHighlighter.Rules:
            i = regex.indexIn(text)
            while i >= 0:
                length = regex.matchedLength()
                self.setFormat(i, length,
                               PythonHighlighter.Formats[format])
                i = regex.indexIn(text, i + length)

        self.setCurrentBlockState(NORMAL)

        if self.stringRe.indexIn(text) != -1:
            return
        # This is fooled by triple quotes inside single quoted strings
        for i, state in ((self.tripleSingleRe.indexIn(text),
                          TRIPLESINGLE),
                         (self.tripleDoubleRe.indexIn(text),
                          TRIPLEDOUBLE)):
            if self.previousBlockState() == state:
                if i == -1:
                    i = len(text)
                    self.setCurrentBlockState(state)
                self.setFormat(0, i + 3,     
                               PythonHighlighter.Formats["string"])
            elif i > -1:
                self.setCurrentBlockState(state)
                self.setFormat(i, len(text),
                               PythonHighlighter.Formats["string"])

    def rehighlight(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QSyntaxHighlighter.rehighlight(self)
        QApplication.restoreOverrideCursor()
        