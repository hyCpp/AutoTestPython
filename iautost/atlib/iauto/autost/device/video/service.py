import os
import asyncore
import json
import six
import struct
import base64
import ctypes
import time
import cv2
import pickle
import threading

HEADER_SIZE = 4

class CStreamService:
    _instance = None
    @staticmethod
    def instance():
        if CStreamService._instance is None:
            CStreamService._instance = CStreamService()
        return CStreamService._instance
    
    def __init__(self):
        self.frame = None
        self.stream_service_on = False
    
    def __del__(self):
        self.stop_stream_service()
    
    def start_stream_service(self, frame_handle=None, daemon=True, asyn=True):
        if not self.stream_service_on:
            self.stream_service_on = True
            if not asyn:
                self.stream_service(frame_handle, daemon)
            else:
                objThread = threading.Thread(target=self.stream_service, args=(frame_handle, daemon))
                objThread.setDaemon(True)
                objThread.start()
    
    def stream_service(self, frame_handle, daemon):
        while 1:
            #
            video = 'rtsp://192.168.5.111:8554/test'
            cap = cv2.VideoCapture(video)
            while self.stream_service_on and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    self.frame = None
                    if frame_handle:
                        frame_handle(self.frame)
                    break
                else:
                    self.frame = frame
                    if frame_handle:
                        frame_handle(self.frame)
                    cv2.waitKey(1)
            else:
                cap.release()
            
            #
            if not daemon or not self.stream_service_on:
                break
            else:
                time.sleep(0.1)
    
    def stop_stream_service(self):
        self.stream_service_on = False

class CPort(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket()
        self.socket.settimeout(0)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accepted(self, sock, addr):
        print('Stream connection from %s' % repr(addr))
        session = CSession(sock)

class CSession(asyncore.dispatcher_with_send):
    def handle_read(self):
        msg = self.recv(8192)
        if msg:
            length, msg = self.unpack(msg)
            #print('receive msg:', msg)
            response = CHandler.instance().handle(msg)
            self.send(response)
    
    def send(self, msg):
        #print('send msg:', str(msg)[:100])
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
    
    def handle(self, msg):
        try:
            if isinstance(msg, six.binary_type):
                msg = msg.decode('utf8')
            data = json.loads(msg)
            
            method = data.get('method')
            result = self.handle_method(method) or ''
            response = {
                        "id": data["id"],
                        "result": result
                        }
            return json.dumps(response)
        except:
            import traceback
            print(traceback.format_exc())
    
    def handle_method(self, method):
        method_mapping = {
                          'snapshot': self.snapshot,
                          }
        method_func = method_mapping.get(method.lower())
        return method_func()
    
    def snapshot(self):
        for _ in range(10):
            frame = CStreamService.instance().frame
            if frame is not None:
                break
            else:
                time.sleep(0.1)
        if frame is None:
            return u''
        else:
            img_serial = str(base64.b64encode(pickle.dumps(frame, protocol=0)), encoding='utf8')
            return img_serial
            #img_serial = pickle.dumps(frame, protocol=0)
            #cache = os.path.sep.join([os.path.dirname(__file__), 'screen.txt'])
            #with open(cache, 'wb') as f:
            #    f.write(img_serial)
            #    f.close()
            #return cache

def do(frame_handle=None, daemon=True, asyn=True):
    print('StreamService Listenning...')
    CStreamService.instance().start_stream_service(frame_handle, daemon, asyn)
    CPort('127.0.0.1', 9302)

def run(frame_handle=None, daemon=True, asyn=True):
    objThread = threading.Thread(target=do, args=(frame_handle, daemon, asyn))
    objThread.setDaemon(True)
    objThread.start()

def stop():
    CStreamService.instance().stop_stream_service()

def start():
    service_file = os.path.abspath(__file__)
    #cmd = 'start /b python "%s"' % service_file
    #os.system(cmd)
    import subprocess
    subprocess.Popen(['python', service_file])

if __name__ == '__main__':
    do(asyn=False)
    asyncore.loop(timeout=0.5)
