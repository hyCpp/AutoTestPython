# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-8-6

@author: wushengbing
'''
import os
import pythoncom
from win32com.shell import shell
from win32com.shell import shellcon


def createShortcut(filename, lnkname, iconname=None):
    shortcut = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, 
                                          None,
                                          pythoncom.CLSCTX_INPROC_SERVER, 
                                          shell.IID_IShellLink)
    shortcut.SetPath(filename)
    if iconname:
        shortcut.SetIconLocation(iconname, 0)
    if os.path.splitext(lnkname)[-1] != '.lnk':
        lnkname += ".lnk"
    shortcut.QueryInterface(pythoncom.IID_IPersistFile).Save(lnkname,0)

def getShortcutDestination(lnk):
    shortcut = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, 
                                          None,
                                          pythoncom.CLSCTX_INPROC_SERVER, 
                                          shell.IID_IShellLink)
    persistant_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
    persistant_file.Load(lnk)
    shortcut.Resolve(0, 0)
    destination = shortcut.GetPath(shell.SLGP_UNCPRIORITY)[0]
    return destination

