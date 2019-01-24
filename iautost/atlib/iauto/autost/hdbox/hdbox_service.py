import os
import asyncore
import json
import six
import struct
import base64
import ctypes

DLL_FOLDER = __file__[:__file__.rfind(os.path.sep)]
os.environ["PATH"] = ";".join([DLL_FOLDER,os.environ["PATH"]])
DLL_FILE = "ATE_PowerControl.dll"

HEADER_SIZE = 4

class CPort(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket()
        self.socket.settimeout(0)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accepted(self, sock, addr):
        print('Incoming connection from %s' % repr(addr))
        session = CSession(sock)

class CSession(asyncore.dispatcher_with_send):
    def handle_read(self):
        msg = self.recv(8192)
        if msg:
            length, msg = self.unpack(msg)
            print('receive msg:', msg)
            response = CHandler.instance().handle(msg)
            self.send(response)
    
    def send(self, msg):
        print('send msg:', msg)
        msg = self.pack(msg)
        super(CSession, self).send(msg)
    
    @staticmethod
    def pack(content):
        """ content should be str
        """
        if isinstance(content, six.text_type):
            content = content.encode("utf-8")
        return struct.pack('i', len(content)) + content

    @staticmethod
    def unpack(data):
        """ return length, content
        """
        length = struct.unpack('i', data[0:HEADER_SIZE])
        return length[0], data[HEADER_SIZE:]

class CHandler:
    _instance = None
    @staticmethod
    def instance():
        if CHandler._instance is None:
            CHandler._instance = CHandler()
        return CHandler._instance
    
    def __init__(self):
        self.dll = ctypes.cdll.LoadLibrary(DLL_FILE)
        result = self.dll.PowerControlOpen()
        if result != 0:
            raise RuntimeError('unable to connect to tbox, please check usb...')
    
    def __del__(self):
        self.dll.PowerControlClose()
    
    def handle(self, msg):
        try:
            if isinstance(msg, six.binary_type):
                msg = msg.decode('utf8')
            data = json.loads(msg)
            
            method = data.get('method')
            if method:
                result = self.handle_method(method)
                if result:
                    #retry, may be usb was disconnected and reconnected
                    self.dll.PowerControlClose()
                    self.dll.PowerControlOpen()
                    result = self.handle_method(method)
            else:
                result = 'default response content.'
            response = {
                        "id": data["id"],
                        "result": result
                        }
            
            return json.dumps(response)
        except:
            import traceback
            print(traceback.format_exc())
    
    def handle_method(self, method):
        if method.find('(') < 0:
            func = method.lower()
            args = ()
        else:
            func = method[ : method.find('(')].lower()
            args = method[method.find('(') + 1 : method.find(')')].split(',')
        method_mapping = {
                          'boot': self.boot,
                          'halt': self.halt,
                          'reboot': self.reboot,
                          'bup_on': self.bup_on,
                          'bup_off': self.bup_off,
                          'acc_on': self.acc_on,
                          'acc_off': self.acc_off,
                          'rev_on': self.rev_on,
                          'rev_off': self.rev_off,
                          'ig_on': self.ig_on,
                          'ig_off': self.ig_off,
                          'ill_on': self.ill_on,
                          'ill_off': self.ill_off,
                          'ill_down': self.ill_down,
                          'pkb_on': self.pkb_on,
                          'pkb_off': self.pkb_off,
                          'spd_speed': self.spd_speed,
                          'usb_on': self.usb_on,
                          'usb_off': self.usb_off,
                          }
        method_func = method_mapping.get(func)
        return method_func(*args)

    def bup_on(self):
        return self.dll.BUP_ON()
    
    def bup_off(self):
        return self.dll.BUP_OFF()
    
    def acc_on(self):
        return self.dll.ACC_ON()
        
    def acc_off(self):
        return self.dll.ACC_OFF()
    
    def rev_on(self):
        return self.dll.REV_ON()
        
    def rev_off(self):
        return self.dll.REV_OFF()
    
    def pkb_on(self):
        return self.dll.PKB_ON()
        
    def pkb_off(self):
        return self.dll.PKB_OFF()
    
    def ig_on(self):
        return self.dll.IG_ON()
        
    def ig_off(self):
        return self.dll.IG_OFF()
    
    def ill_on(self):
        return self.dll.ILL_ON()
        
    def ill_off(self):
        return self.dll.ILL_OFF()
    
    def ill_down(self, hz, val):
        class CPara(ctypes.Structure):
            _fields_ = [("Hz", ctypes.c_int), ("Val", ctypes.c_int)]
        return self.dll.ILL_DOWN(ctypes.byref(CPara(int(hz), int(val))))
        
    def spd_speed(self, speed):
        result = self.dll.SPD_SPEED(ctypes.byref(ctypes.c_int(int(speed))))
    
    def usb_on(self, port):
        result = self.dll.USB_ON(ctypes.byref(ctypes.c_int(int(port))))
        return result
    
    def usb_off(self, port):
        result = self.dll.USB_OFF(ctypes.byref(ctypes.c_int(int(port))))
        return result
    
    def boot(self):
        result = self.dll.BUP_ON()
        result |= self.dll.ACC_ON()
        return result
    
    def halt(self):
        result = self.dll.BUP_OFF()
        result |= self.dll.ACC_OFF()
        return result
    
    def reboot(self):
        result = self.halt()
        result |= self.boot()
        return result

def run():
    print('Tbox Listenning...')
    #CHandler.instance()
    CPort('127.0.0.1', 9301)
    asyncore.loop(timeout=0.5)

if __name__ == '__main__':
    run()
