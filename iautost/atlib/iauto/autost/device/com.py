# -*- coding: utf-8 -*-

import time
import platform
import serial
import serial.tools.list_ports

class CSerial:
    objInstance = None
    @staticmethod
    def instance():
        if CSerial.objInstance is None:
            CSerial.objInstance = CSerial()
        return CSerial.objInstance
    
    def __init__(self):
        self.ser = None
        #if platform.system() == 'Windows':
        #    connect_port = 'COM5'
        #else:
        #    connect_port = '/dev/ttyUSB0'
        ports = serial.tools.list_ports.comports()
        for port, description, address in sorted(ports):
            if description.lower().find('usb serial port') >= 0:
                try:
                    self.ser = serial.Serial(port, baudrate=460800, timeout=0.5)
                    break
                except:
                    continue
        
        #
        if self.ser is None:
            raise RuntimeError('serial connection error...')
        
    def __del__(self):
        if self.ser:
            self.ser.close()
    
    def isDeviceOn(self):
        return self.ser is not None and self.ser.isOpen()
    
    def waitUntilDeviceOn(self, timeout=5.0, interval=1.0):
        start_time = time.time()
        while True:
            if self.isDeviceOn():
                break
            else:
                self.ser.open()
            
            if (time.time() - start_time) > timeout:
                raise RuntimeError('serial timeout...')
            else:
                time.sleep(interval)
    
    def send_cmd(self, cmd, timeout=1.0):
        self.ser.write((cmd+'\n').encode('utf8'))
        response = ""
        start_time = time.time()
        while (time.time() - start_time) <= timeout:
            data = self.ser.readline()
            if data:
                if response:
                    response += data
                else:
                    response = data
            else:
                break
        try:
            response = response.decode('utf8')
        except:
            response = ""
        return response
    
    def shell(self, cmd, timeout=5.0, return_mark=''):
        print(cmd)
        response = self.send_cmd(cmd, timeout=0.1)
        start_time = time.time()
        while (time.time() - start_time) <= timeout:
            data = self.ser.readline()
            if data:
                response += data.decode('utf8')
            if not return_mark:
                return response
            if response and response.find(return_mark) >= 0:
                return response
        else:
            #raise RuntimeError('serial shell timeout...')
            return ''
    
    def _isTestServiceOn(self):
        cmd = 'ps | grep iauto2test'
        response = self.send_cmd(cmd)
        if response.find('/data/iauto2test') != -1:
            return True
        else:
            return False
    
    def _startTestService(self):
        response = self.send_cmd('/data/iauto2test &')
        if response.find('auto_test on') != -1:
            return True
        else:
            return False
    
    def startTestService(self, timeout=5.0, interval=1.0):
        start_time = time.time()
        while True:
            if self._isTestServiceOn():
                break
            else:
                self._startTestService()
            
            if (time.time() - start_time) > timeout:
                raise RuntimeError('auto test service timeout...')
            else:
                time.sleep(interval)
    
    def _isADBServiceOn(self):
        cmd = 'ps | grep adbd'
        response = self.send_cmd(cmd)
        if response.find('/sbin/adbd') != -1:
            return True
        else:
            return False
    
    def _startADBService(self):
        self.send_cmd('start adbd')
        return True
    
    def startADBService(self, timeout=5.0, interval=1.0):
        start_time = time.time()
        while True:
            if self._isADBServiceOn():
                break
            else:
                self._startADBService()
            
            if (time.time() - start_time) > timeout:
                raise RuntimeError('adb service timeout...')
            else:
                time.sleep(interval)
    
    def _isStreamServiceOn(self):
        cmd = 'ps | grep streamservice'
        response = self.send_cmd(cmd)
        #print(response)
        if response.find('Teststreamservice') != -1:
            return True
        else:
            return False
    
    def _startStreamService(self):
        self.shell('mount -o remount rw /', return_mark='#')
        self.shell('mount -o remount rw /system', return_mark='#')
        self.shell('cp /data/stream/* /lib/', return_mark='#')
        self.shell('sync', return_mark='#')
        self.shell('cd /lib; ./stream_so_link.sh', return_mark='#')
        self.shell("ps |grep stream |awk '{print $2}' |xargs kill -9", return_mark='#')
        self.shell('iptables -F', return_mark='#')
        self.shell('iptables -P INPUT ACCEPT', return_mark='#')
        self.shell('iptables -P OUTPUT ACCEPT', return_mark='#')
        self.shell('/usr/bin/streamservice &', return_mark='#')
        self.shell('Teststreamservice &', return_mark='quit', timeout=10.0)
    
    def startStreamService(self, timeout=20.0, interval=1.0):
        start_time = time.time()
        while True:
            self._startStreamService()
            if self._isStreamServiceOn():
                break

            if (time.time() - start_time) > timeout:
                raise RuntimeError('Teststreamservice timeout...')
            else:
                time.sleep(interval)
    
if __name__ == '__main__':
    objSerial = CSerial.instance()
    objSerial.waitUntilDeviceOn()
    objSerial.startService()
    
    