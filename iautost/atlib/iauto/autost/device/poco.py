# -*- coding: utf-8 -*-

from poco import Poco
from poco.agent import PocoAgent
from poco.drivers.std.attributor import StdAttributor
from poco.drivers.std.dumper import StdDumper
from poco.drivers.std.screen import StdScreen
from poco.freezeui.hierarchy import FrozenUIHierarchy
from poco.utils.airtest import AirtestInput

#from airtest.core.api import *
#from airtest.core.api import device as current_device
from airtest.core.helper import device_platform
from autost.api import *


class iAutoDumper(StdDumper):
    def __init__(self, rpcclient):
        super(iAutoDumper, self).__init__(rpcclient)

    def dumpHierarchy(self, onlyVisibleNode=True):
        return device().dump(onlyVisibleNode=True)

class iAutoPocoAgent(PocoAgent):
    def __init__(self, rpc):
        #self.c = RPC(addr)
        self.c = rpc
        hierarchy = FrozenUIHierarchy(iAutoDumper(self.c), StdAttributor(self.c))
        screen = StdScreen(self.c)
        input = AirtestInput()
        super(iAutoPocoAgent, self).__init__(hierarchy, input, screen, None)

class iAutoPoco(Poco):
    _instance = None
    @staticmethod
    def instance():
        if iAutoPoco._instance is None:
            iAutoPoco._instance = iAutoPoco()
        return iAutoPoco._instance
    
    def __init__(self, ip='192.168.36.18', port=5391, connect_default_device=True, **kwargs):
        if connect_default_device and not device():
            # currently only connect to Android as default
            # can apply auto detection in the future
            connect_device("iauto:///?%s&%s" % (ip,port))

        # always forward for android device to avoid network unreachable
        if device_platform() == 'Android':
            local_port, _ = device.adb.setup_forward('tcp:{}'.format(port))
            ip = 'localhost'
            port = local_port
        elif device_platform() == 'IOS':
            ip = device.get_ip_address()
            port = port
            
        if not ip:
            import socket
            ip = socket.gethostbyname(socket.gethostname())
            # Note: ios is not support for now.

        agent = iAutoPocoAgent(device().rpc)
        super(iAutoPoco, self).__init__(agent, **kwargs)
    