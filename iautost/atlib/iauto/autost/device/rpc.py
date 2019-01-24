# -*- coding: utf-8 -*-

from poco.utils.simplerpc.rpcclient import RpcClient
from poco.utils.simplerpc.transport.tcp.main import TcpClient
from poco.utils.simplerpc.utils import sync_wrapper

class RPC(RpcClient):
    def __init__(self, addr):
        conn = TcpClient(addr)
        #conn.prot = RawProtocolFilter()
        super(RPC, self).__init__(conn)
        
        self.DEBUG = False
    
    def isConnected(self):
        return self._status == self.CONNECTED
    
    @sync_wrapper
    def call(self, func, *args, **kwargs):
        return super(RPC, self).call(func, *args, **kwargs)
    
    @sync_wrapper
    def call2(self, callback, func, *args, **kwargs):
        msg, cb = self.format_request(func, *args, **kwargs)
        cb.on_result(callback)
        self.conn.send(msg)
        return cb

class RawProtocolFilter(object):
    def __init__(self):
        super(RawProtocolFilter, self).__init__()
        self.buf = b''

    def input(self, data):
        """ 小数据片段拼接成完整数据包
            如果内容足够则yield数据包
        """
        self.buf += data
        while len(self.buf) > 0:
            content = self.buf[:]
            self.buf = b''
            yield content

    @staticmethod
    def pack(content):
        import six
        if isinstance(content, six.text_type):
            content = content.encode("utf-8")
        return content

    @staticmethod
    def unpack(data):
        return data