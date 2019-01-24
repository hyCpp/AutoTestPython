# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-6-29

@author: wushengbing
'''
from HTMLParser import HTMLParser
import traceback

 
class CHTMLParser(HTMLParser):
    def __init__(self, template_paras):
        super(CHTMLParser, self).__init__()
        self.template_paras = template_paras
        self.__text = []
 
    def handle_data(self, data):
        data = data.replace(' G_T ', '>').replace(' L_T ', '<').replace(' Q_U_O_T ', '"').replace(' AND_AND ', '&')
        if len(data) > 0:
            self.__text.append(data)

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.__text = []
        if tag == 'img':
            for k, v in attrs:
                if k == 'src':
                    if '/' in v:
                        img_name = v.split('/')[-1]
                    elif '\\' in v:
                        img_name = v.split('\\')[-1]
                    else:
                        img_name = v
                else:
                    pass
            paras = self.template_paras.get(img_name, None)
            if paras:
                self.__text.append("Template('%s',%s)" % (img_name, paras))
            else:
                self.__text.append("Template('%s')" % img_name)

    def handle_endtag(self, tag):
        if tag == 'html':
            self.__text = self.__text[1:]

    def text(self):
        return ''.join(self.__text)
 

def html2text(data, template_paras={}):
    data = data.replace('&gt;', ' G_T ').replace('&lt;', ' L_T ').replace('&quot;', ' Q_U_O_T ').replace('&amp;', ' AND_AND ')
    try:
        parser = CHTMLParser(template_paras)
        parser.feed(data)
        parser.close()
        return parser.text()
    except:
        print(traceback.print_exc())

