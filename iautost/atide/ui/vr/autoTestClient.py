import socket
import time
import threading
import json
from  . vrServerMsgTask import *

BUF_SIZE = 1024


class VrClient():

    def __init__(self, parent=None, path_prefix="C:\\temp\\"):
        self.ide = parent
        self.connected = False
        self.running = True
        self.file_saving = False
        self.recvThread = threading.Thread(target=self.__recv, name='RecvThread')
        self.msg_task_queue = vrServerMsgTask()
        self.path_prefix = path_prefix

    def connect(self, host, port):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.client.connect((host, int(port)))
        except socket.error as e:
            # ConnectionRefusedError
            print("[Connect error]: %s" % e)
            return False
        else:
            self.recvThread.start()
            self.msg_task_queue.start()
            print("connect success")
            self.connected = True
            self.register()
            return True

    def disconnect(self):
        self.client.close()
        self.connected = False

    def register(self):
        dict_regi = {'type':'SIGNCLIENT', 'data':{'category':'237b', 'area':'CH', 'lang':'chn,end'}}
        data = self.encode(dict_regi)
        self.send(data)

    def send(self, content):
        try:
            size = self.client.send(content.encode())
        except socket.error as e:
            print("[Send error]: %s" % e)
            return -1
        else:
            return size

    def __recv(self):
        print("%s start..." % threading.current_thread().name)
        while self.running is True:
            try:
                buff = self.client.recv(BUF_SIZE)
            except socket.error as e:
                print("[Receive error]: %s" % e)
                self.running = False
            else:
                recv_str = buff.decode()
                #判断接收的数据是否为json格式，如果不是，则可能是传过来的文件或者无用数据，进行进一步判断
                try:
                    recv_dict = json.loads(recv_str)
                except json.decoder.JSONDecodeError as e:
                    #json decoder 认为当前数据不是json格式
                    if self.file_saving is True:
                        self.file_write(buff)
                    else:
                        self.running = False
                else:
                    #接收到的Json 字符串，进行进一步处理，目前是测试用的逻辑
                    if  'filename' in recv_dict:
                        print(recv_dict["status"])
                        #判断文件是否传输完毕
                        if recv_dict["status"]=="finish":
                            self.file_saving = False
                        elif recv_dict["status"]=="start":
                            self.file_saving = True
                            ready_str = {"ready":True}
                            self.filename = self.path_prefix+"\\"+recv_dict["filename"]
                            self.send(self.encode(ready_str))
                        else:
                            # 可能会有其他状态，暂时留空
                            pass
                    else:
                        self.msg_task_queue.process_message(recv_str)
            time.sleep(1)
        print("%s ended" % threading.current_thread().name)
        self.disconnect()

    def file_write(self, buff):
        print("write %s" % buff)
        with open(self.filename, 'ab+') as f:
            f.write(buff)

    def stop(self):
        self.running = False
        self.msg_task_queue.stop_thread()
        print("try to stop")

    @staticmethod
    def encode(data):
        return json.dumps(data)

    @staticmethod
    def decode(data):
        return json.loads(data)


if __name__ == '__main__':
    data = {"hello": "world"}
    clt = VrClient()
    ret = clt.connect('192.168.64.53', 9889)

    #if ret is True:
        #clt.register()

#        clt.stop()
#        clt.disconnect()
