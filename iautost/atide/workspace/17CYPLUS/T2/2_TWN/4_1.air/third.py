# -*- coding: utf-8 -*-

from autost.api import *

G.DEVICE_URI='iauto:///?ip=192.168.5.111&port=5391'
#G.DEVICE_URI='iauto:///?ip=192.168.36.18&port=5391'
#G.DEVICE_URI='iauto:///?ip=127.0.0.1&port=5391'
connect_device(G.DEVICE_URI)

poco = iAutoPoco()
poco(text="AM").click()

