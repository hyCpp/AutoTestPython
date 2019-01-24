# -*- coding: utf-8 -*-

import os
import six
import json
import ctypes
import base64
import pickle

import autost.device.rpc
import autost.device.video.service

def snapshot():
    img_serial = CServiceClient.instance().call('snapshot')
    #img_serial = open(img_serial, 'rb').read()
    if not img_serial:
        raise RuntimeError('fail to snapshot...')
    img_serial = base64.b64decode(img_serial)
    img = pickle.loads(img_serial)
    return img

class CServiceClient:
    _instance = None
    @staticmethod
    def instance():
        if CServiceClient._instance is None:
            CServiceClient._instance = CServiceClient()
        return CServiceClient._instance
    
    def __init__(self, addr=('127.0.0.1', 9302)):
        self.addr = addr
        self.rpc = None
    
    def rpc_connect(self):
        try:
            self.rpc = autost.device.rpc.RPC(self.addr)
            self.rpc.wait_connected()
        except RuntimeError:
            #import traceback
            #print(traceback.format_exc())
            autost.device.video.service.start()
            for i in range(20):
                try:
                    self.rpc = autost.device.rpc.RPC(self.addr)
                    self.rpc.wait_connected()
                    break
                except RuntimeError:
                    if i < 10:
                        pass
                    else:
                        raise RuntimeError('unable to connect to tbox service...')
    
    def __del__(self):
        self.rpc.close()
    
    def call(self, method):
        if self.rpc is None or not self.rpc.isConnected():
            self.rpc_connect()
        return self.rpc.call(method)

if __name__ == '__main__':
    print(CServiceClient(addr=('127.0.0.1', 9302)).call('boot'))
