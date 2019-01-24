# -*- coding: utf-8 -*-

import os
import six
import json
import ctypes
import autost.device.rpc

DLL_FOLDER = __file__[:__file__.rfind(os.path.sep)]
os.environ["PATH"] = ";".join([DLL_FOLDER,os.environ["PATH"]])
DLL_FILE = "ATE_PowerControl.dll"

def bup_on():
    return CService.instance().call('bup_on')

def bup_off():
    return CService.instance().call('bup_off')

def acc_on():
    return CService.instance().call('acc_on')

def acc_off():
    return CService.instance().call('acc_off')

def boot():
    return CService.instance().call('boot')

def halt():
    return CService.instance().call('halt')

def reboot():
    return CService.instance().call('reboot')

def rev_on():
    return CService.instance().call('rev_on')

def rev_off():
    return CService.instance().call('rev_off')

def ig_on():
    return CService.instance().call('ig_on')

def ig_off():
    return CService.instance().call('ig_off')

def ill_on():
    return CService.instance().call('ill_on')

def ill_off():
    return CService.instance().call('ill_off')

def ill_down(hz, val):
    return CService.instance().call('ill_down(%s,%s)' % (str(hz), str(val)))

def pkb_on():
    return CService.instance().call('pkb_on')

def pkb_off():
    return CService.instance().call('pkb_off')

def spd_speed(speed):
    return CService.instance().call('spd_speed(%s)' % (str(speed)))

def usb_on(port):
    return CService.instance().call('usb_on(%s)' % (str(port)))

def usb_off(port):
    return CService.instance().call('usb_off(%s)' % (str(port)))

class CService:
    _instance = None
    @staticmethod
    def instance():
        if CService._instance is None:
            CService._instance = CService()
        return CService._instance
    
    def __init__(self, addr=('127.0.0.1', 9301)):
        self.addr = addr
        self.rpc = None
    
    def rpc_connect(self):
        try:
            self.rpc = autost.device.rpc.RPC(self.addr)
            self.rpc.wait_connected()
        except RuntimeError:
            start_tbox_service()
            for i in range(20):
                try:
                    self.rpc = autost.device.rpc.RPC(self.addr)
                    self.rpc.wait_connected()
                    break
                except RuntimeError:
                    if i < 19:
                        pass
                    else:
                        raise RuntimeError('unable to connect to tbox service...')
    
    def __del__(self):
        self.rpc.close()
    
    def call(self, method):
        if self.rpc is None or not self.rpc.isConnected():
            self.rpc_connect()
        return self.rpc.call(method)

def start_tbox_service():
    #from multiprocessing import Process
    #process = Process(target=tbox_service)
    #process.start()
    #import threading
    #process = threading.Thread(target=tbox_service)
    #process.start()
    tbox_service()
    #import time
    #time.sleep(3.0)
    
def tbox_service():
    service_file = os.path.sep.join([os.path.dirname(__file__), 'hdbox_service.pyc'])
    if not os.path.exists(service_file):
        service_file = os.path.sep.join([os.path.dirname(__file__), 'hdbox_service.py'])
    #cmd = 'start /b python "%s"' % service_file
    #os.system(cmd)
    import subprocess
    subprocess.Popen(['python', service_file])

if __name__ == '__main__':
    print(CService(addr=('127.0.0.1', 9301)).call('boot'))
