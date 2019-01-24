# -*- coding: utf-8 -*-

import os
import json
import time
import base64
import cv2
import threading
import win32pipe
import win32file
import socket
import struct

import airtest.core.android.rotation
from airtest.core.api import *
from airtest.core.android.android import Android
from airtest.core.android.minitouch import *
from airtest.core.helper import G
from airtest import aircv


class iAndroid(Android):
    """iAuto Android Device Class"""
    def __init__(self, serialno=None, 
                 host=('127.0.0.1', 5037), 
                 touch_method='ADBTOUCH',
                 stream_method='MINICAP'):
        #
        self.serialno = serialno
        self.host = host
        self.stream_method = stream_method
        
        #
        try:
            super(iAndroid, self).__init__(serialno, host, touch_method=touch_method)
        except IndexError:
            if not hasattr(self, serialno):
                raise RuntimeError("no adb devices...")
    
    def __del__(self):
        self.disconnect()
    
    def connect(self):
        try:
            self.adb.shell('touch /data/A2Tserver_on')
        except:
            pass
    
    def disconnect(self):
        pass
        #if hasattr(self, 'rotation_watcher'):
        #    self.rotation_watcher.teardown()
        #airtest.core.android.rotation.LOGGING = None
        #if hasattr(self, 'minicap'):
        #    self.minicap.teardown_stream()
    
    def get_stream(self):
        if self.stream_method.upper() == 'MINICAP':
            stream_func = self._get_stream_minicap
        elif self.stream_method.upper() == 'SCRCPY':
            stream_func = self._get_stream_scrcpy
        else:
            stream_func = self._get_stream_snapshot
        try:
            for frame in stream_func():
                yield frame
        except Exception as e:
            print(e)
            yield None
    
    def _get_stream_snapshot(self):
        while 1:
            yield self.snapshot()
    
    def _get_stream_minicap(self):
        for screen in self.minicap.get_stream():
            if screen is not None:
                frame = aircv.utils.string_2_img(screen)
                yield frame
            else:
                yield None
                break
    
    def _get_stream_scrcpy(self):
        #
        env_dir = os.path.sep.join([__file__[:__file__.rfind(os.path.sep)], 'env'])
        scrcpy_src = os.path.sep.join([env_dir, 'Android', 'data', 'local', 'tmp', 'scrcpy-server.jar'])
        scrcpy_dst = '/data/local/tmp/scrcpy-server.jar'
        self.adb.push(scrcpy_src, scrcpy_dst)
        self.adb.shell('chmod -R 777 %s' % scrcpy_dst)
        self.adb.start_shell('CLASSPATH=/data/local/tmp/scrcpy-server.jar app_process / com.genymobile.scrcpy.Server 0 8000000 true')
        
        #
        try:
            self.adb.forward('tcp:8080', 'localabstract:scrcpy')
        except:
            pass
        #
        PIPE_NAME = r'\\.\pipe\my_pipe'
        self.pipe = win32pipe.CreateNamedPipe(PIPE_NAME,
                                              win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED,
                                              win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_WAIT,
                                              win32pipe.PIPE_UNLIMITED_INSTANCES, 128, 64, 0, None)
        pipe_thread = threading.Thread(target=self._socket_2_pipe)
        pipe_thread.setDaemon(True)
        pipe_thread.start()
        
        cap = cv2.VideoCapture(PIPE_NAME)
        #print('video capture...')
        #cap = cv2.VideoCapture('http://127.0.0.1:8080')
        #print('cap.isOpened()', cap.isOpened())
        #i = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                yield frame
                break
            else:
                #i += 1
                #print('get frame', i)
                #cv2.imshow("frame", frame)
                cv2.waitKey(1)
                yield frame
        else:
            cap.release()
            yield None
    
    def _socket_2_pipe(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 8080))
        dummy = sock.recv(1)
        deviceName = sock.recv(64)
        width = sock.recv(2)
        height = sock.recv(2)
        #print(deviceName.decode("utf-8").strip())
        #print(struct.unpack(">H", width))
        #print(struct.unpack(">H", height))
        
        win32pipe.ConnectNamedPipe(self.pipe, None)
#        start_time = time.time()
        buffer_size = 0
        while 1:
#            if time.time() - start_time > 3:
#                break
            data = sock.recv(4096)
            if not data:
                break
            #print('prepare data', len(data))
            win32file.WriteFile(self.pipe, data)
            buffer_size += len(data)
            #print('send data', buffer_size, len(data))
        sock.close()
        win32pipe.DisconnectNamedPipe(self.pipe)
    
    def dump(self, onlyVisibleNode=True):
        data = {}
        if self.adb.exists_file('/data/DumpTree'):
            data = self.adb.shell('cat /data/DumpTree')
        #data = self.adb.shell('ls')
        #print('=====================')
        #print(data)
        #print('=====================')
        if type(data) == type(''):
            data = json.loads(data)
        
        root = self._restruct_hierarchy(data)
#         print('=====================')
#         print(root)
#         print('=====================')
        return root
    
    def _restruct_hierarchy(self, data, node={}):
        #
        payload = data.get('payload') or {}
        if 'transparent' in payload:
            wx = payload.get('width')
            wy = payload.get('height')
            sx, sy = self.get_current_resolution()
            scale = min(sx / wx, sy / wy)
            root = self._restruct_hierarchy_sketch(data, node, parent_rect=(0,0,wx,wy), scale=scale)
        else:
            root = self._restruct_hierarchy_17cy(data, node)
            children = root.get('children') or []
            if len(children) == 2:
                screen = children[0].get('payload').get('objectName')
                view = children[1].get('payload').get('objectName')
                if not screen:
                    root['payload']['objectName'] = view
                else:
                    root['payload']['objectName'] = '%s/%s' % (screen, view)
        
        #
        return root
    
    def _restruct_hierarchy_sketch(self, data, node={}, parent_rect=(0,0,1280,680), scale=1.0):
        #
        node['payload'] = {}
        node['payload']['visible'] = False
        node['payload']['objectName'] = data.get('part') or ""
        
        # payload
        x1, y1, x2, y2 = parent_rect
        payload = data.get('payload') or {}
        if payload:
            #
            for key, value in payload.items():
                if key in ('x','y','width','height','child','visible',):
                    if key in ('visible',):
                        node['payload'][key] = value
                        #node['payload']['is_visible'] = value
                    continue
                elif key in ('text', ):
                    if type(value) == type(""):
                        node['payload'][key] = value
                    else:
                        text_list = []
                        for t in value:
                            for k, v in t.items():
                                if v:
                                    text_list.append(v)
                        if text_list:
                            text = ' '.join(text_list)
                            node['payload'][key] = text
                else:
                    node['payload'][key] = value
                    #if key == 'type':
                    #    print('type =', value)
            
            #
            screen_w, screen_h = self.get_current_resolution()
            if 'x' in payload:
                x = payload['x']
                y = payload['y']
                if 'width' in payload:
                    dx = payload['width']
                    dy = payload['height']
                    x1, y1, x2, y2 = (
                                      x if x >= x1 else x1, 
                                      y if y >= y1 else y1, 
                                      x + dx if x + dx <= x2 else x2, 
                                      y + dy if y + dy <= y2 else y2
                                      )
                    dx = x2 - x1
                    dy = y2 - y1
                    x, y = x1 + dx / 2, y1 + dy / 2
                    if not payload.get('transparent') and payload.get('className') != 'BasicControl/NXFrame':
                        node['payload']['size'] = (int(dx * scale), int(dy * scale))
                    else:
                        node['payload']['size'] = (0, 0)
                        
                node['payload']['pos'] = (x * scale / screen_w, y * scale / screen_h)
        
        # children
        children = data.get('child') or data.get('children') or []
        if children:
            node['children'] = []
            
            for child in children:
                if child:
                    child_node = self._restruct_hierarchy_sketch(child, {}, (x1, y1, x2, y2), scale)
                    if child_node and child_node['payload']['visible']:
                        node['children'].append(child_node)
            
            if len(node['children']) > 0:
                node['payload']['visible'] = True
        
        #
        #node['payload']['visible'] = True
        return node
    
    def _restruct_hierarchy_17cy(self, data, node={}):
        #
        node['payload'] = {}
        node['payload']['visible'] = False
        node['payload']['objectName'] = data.get('part') or ""
        
        # payload
        payload = data.get('payload') or {}
        if payload:
            #
            for key, value in payload.items():
                if key in ('x','y','width','height','child','visible',):
                    if key in ('visible',):
                        node['payload'][key] = value
                        #node['payload']['is_visible'] = value
                    continue
                elif key in ('text', ):
                    if type(value) == type(""):
                        node['payload'][key] = value
                    else:
                        text_list = []
                        for t in value:
                            for k, v in t.items():
                                if v:
                                    text_list.append(v)
                        if text_list:
                            text = ' '.join(text_list)
                            node['payload'][key] = text
                else:
                    node['payload'][key] = value
                    #if key == 'type':
                    #    print('type =', value)
            
            #
            screen_w, screen_h = self.get_current_resolution()
            if 'x' in payload:
                if 'width' in payload:
                    x = payload['x'] + payload['width'] / 2
                    y = payload['y'] + payload['height'] / 2
                    node['payload']['size'] = (payload['width'], payload['height'])
                else:
                    x = payload['x']
                    y = payload['y']
                
                node['payload']['pos'] = (x * 1.0 / screen_w, y * 1.0 / screen_h)
        
        # children
        children = data.get('child') or data.get('children') or []
        if children:
            node['children'] = []
            
            for child in children:
                if child:
                    child_node = self._restruct_hierarchy_17cy(child, {})
                    if child_node and child_node['payload']['visible']:
                        node['children'].append(child_node)
            
            if len(node['children']) > 0:
                node['payload']['visible'] = True
        
        #
        #node['payload']['visible'] = True
        return node
    
    def home(self):
        self.unlock()
        super(iAndroid, self).home()
    
    def touch(self, pos, times=1, duration=0.01, **kwargs):
        super(iAndroid, self).touch(pos, times=times, duration=duration)

    def swipe(self, t1, t2, duration=1.0, steps=1, **kwargs):
        super(iAndroid, self).swipe(t1, t2, duration, steps=1)
    
    def flick(self, pos, direction, speed='normal', duration=0.06, steps=5, **kwargs):
        dir1, dir2, mx, my = direction
        topos = pos[0]-mx*20, pos[1]+my*20
        super(iAndroid, self).swipe(pos, topos, duration, steps)
        
    def setup(self, project='android', **kwargs):
        print('auto setup...')
        env_dir = os.path.sep.join([__file__[:__file__.rfind(os.path.sep)], 'env'])
        
        data_dirs = [
                    project,
                    #'_'.join([project, machine]),
                    #'_'.join([project, machine, area]),
                    ]
        for data_dir in data_dirs:
            src_data_dir = os.path.sep.join([env_dir, data_dir])
            self._push_dir(self.adb, src_data_dir, '')
    
    def _push_dir(self, adb, src, dst, exclude_dirs=['__pycache__',], exclude_files=['__init__.py',]):
        if os.path.isdir(src):
            for sub in os.listdir(src):
                sub_src = os.path.sep.join([src, sub])
                sub_dst = '/'.join([dst, sub])
                if os.path.isdir(sub_src):
                    if sub not in exclude_dirs:
                        self._push_dir(adb, sub_src, sub_dst, exclude_dirs, exclude_files)
                if os.path.isfile(sub_src):
                    if sub not in exclude_files:
                        adb.push(sub_src, sub_dst)
                        adb.shell('chmod -R 777 %s' % sub_dst)

G.register_custom_device(iAndroid)

