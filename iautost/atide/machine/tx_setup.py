from autost.api import *

try:
    #
    uri = 'iauto://192.168.5.111:5391/?auto_connect=0'
    #uri = 'iAndroid://127.0.0.1:5037'
    connect_device(uri)
    
    #
    """
    setup example:
        project='17cyplus', machine='t0', area=''
        project='17cyplus', machine='t2', area='uc'
        project='17cysketch', machine='t0', area=''
        project='17cysketch', machine='t2', area='uc'
        project='AndroidPoc', machine='', area=''
    """
    device().setup(project='17cysketch', machine='t0', area='uc')
except:
    import traceback
    print(traceback.print_exc())
    input('press any key to exit...')