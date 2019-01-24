from autost.api import *

try:
    uri = 'iauto://192.168.5.111:5391/?auto_connect=0'
    #uri = 'iAndroid://127.0.0.1:5037'
    connect_device(uri)
    device().wake()
except:
    import traceback
    print(traceback.print_exc())
    input('press any key to exit...')