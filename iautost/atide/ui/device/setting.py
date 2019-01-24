# -*- coding: UTF8 -*-

#DEVICE_URI='iauto://127.0.0.1:5391'
#DEVICE_URI='iauto://192.168.5.111:5391'
DEVICE_URI_LIST = [
                   #'iauto://127.0.0.1:5391/?stream_method=snapshot',
                   #'iauto://192.168.5.111:5391',
                   #'iAndroid://127.0.0.1:5037',
                   
                   # AndroidPoc
                   #'iAndroid://127.0.0.1:5037/?stream_method=SCRCPY',
                   ]
with open('config.txt') as f:
    f.readline()
    config_content = f.read()
    config_dict = eval(config_content)
    DEVICE_URI_LIST += config_dict['DEVICE_URI_LIST']
