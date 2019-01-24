# -*- coding: utf-8 -*-

def set_current_dir():
    import os
    import sys
    maindir = os.path.abspath(sys.argv[0])
    maindir = maindir[:maindir.rfind(os.path.sep)]
    os.chdir(maindir)

if __name__ == '__main__':
    import ctypes  
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("iAutoST")
    #autost_setup()
    set_current_dir()
    import ui.ide
    ui.ide.CIDE().run()
