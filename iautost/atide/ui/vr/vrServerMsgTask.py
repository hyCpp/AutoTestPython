# -*- coding: UTF8 -*-
# !/usr/bin/python

import queue
import threading
import json

class vrServerMsgTask(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.is_running = True
        self.msg_queue = queue.Queue()
        self.msg_condition = threading.Condition()
        self.setDaemon(True)

    def run(self):
        while self.is_running:
            self.msg_condition.acquire()
            if self.msg_queue.empty():
                self.msg_condition.wait()
            while not self.msg_queue.empty():
                data = self.msg_queue.get_nowait()
                if data:
                    self.process_message(data)
            self.msg_condition.release()

    def post_message(self, data):
        self.msg_condition.acquire()
        self.msg_queue.put(data)
        self.msg_condition.notify()
        self.msg_condition.release()

    def process_message(self, data):
        print(data)

    def stop_thread(self):
        if self.isAlive():
            self.is_running = False
