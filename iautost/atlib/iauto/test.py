from autost.api import *

#connect_device('iauto:///?ip=192.168.5.111&port=5391')
#device().setup()

#connect_device('iauto:///?ip=192.168.5.111&port=5391')
#device().wakeup()


#connect_device('iauto:///?ip=192.168.5.111&port=5391')
#snapshot(filename='screen.jpg')


connect_device('iAndroid://127.0.0.1:5037/?stream_method=scrcpy')
#snapshot(filename='screen.jpg')
#device().swipe([138,1057], [147,720])
#device().flick([842,751], ('left','left', -10, 1))


import cv2
for x2 in device().get_stream():
    if x2 is not None:
        cv2.imshow("frame", x2)
        cv2.waitKey(1)