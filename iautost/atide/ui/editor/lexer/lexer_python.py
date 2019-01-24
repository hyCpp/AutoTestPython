# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-5-31

@author: wushengbing
'''
from PyQt5.Qsci import QsciLexerPython
import builtins


BUILTINS_FUNC = ' '.join(dir(builtins))


class CLexerPython(QsciLexerPython):
    
    def __init__(self):
        super(CLexerPython, self).__init__()

    
    def keywords(self, s):
        if s == 2:#HighlightedIdentifier
            return BUILTINS_FUNC
        if s == 1:#Keyword
            return QsciLexerPython.keywords(self, s) + ' self'
        return QsciLexerPython.keywords(self, s)
        
        
if __name__ == '__main__':
    print(BUILTINS_FUNC)