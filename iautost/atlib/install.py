#!/usr/bin/python
'''
Created on 2018-11-6

@author: wushengbing
'''
import os
import sys


def install():
    maindir = os.path.abspath(sys.argv[0])
    maindir = maindir[:maindir.rfind(os.path.sep)]
    atlibdir = os.sep.join([maindir, 'iauto'])
    packages_dir = os.sep.join([maindir, 'third'])
    print(maindir,atlibdir,packages_dir)
    os.chdir(packages_dir)
    if os.path.exists(os.path.join(packages_dir, 'requirement.txt')):
        os.system('pip install -r requirement.txt')
    os.chdir(atlibdir)
    os.system('python setup.py install')
    os.chdir(maindir)    

if __name__ == '__main__':
    install()