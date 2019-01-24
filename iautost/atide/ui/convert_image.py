# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-11-7

@author: wushengbing
'''
import os
import sys
import shutil


def convert():
    data = {}
    maindir = os.path.abspath(sys.argv[0])
    maindir = maindir[:maindir.rfind(os.path.sep)]
    icon_dir = os.sep.join([maindir, 'icon'])
#    new_icon_dir = os.sep.join([maindir, 'icon_new'])
#    if os.path.isdir(new_icon_dir):
#        shutil.rmtree(new_icon_dir)
#    os.mkdir(new_icon_dir)
    for file in os.listdir(icon_dir):
        if file.endswith('.png'):
            f_path = os.path.join(icon_dir, file)
#            new_f_path = os.path.join(new_icon_dir, file)
            try:
                print(f_path)
                os.system('convert %s -strip %s' % (f_path, f_path))
            except:
                import traceback
                print(traceback.print_exc())

def generate():
    os.system('pyrcc5 -o res.py res.qrc')


if __name__ == '__main__':
    convert()
    generate()
