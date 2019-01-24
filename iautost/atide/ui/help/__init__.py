# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-9-29

@author: wushengbing
'''
import webbrowser


def openHtml(html_file):
    try:
        webbrowser.open(html_file)
    except:
        pass