# -*- coding: utf-8 -*-

import os
import json
import time
import base64
import cv2
import threading

from airtest.core.api import *
from airtest.core.device import Device
from airtest.core.helper import G
from airtest import aircv

from .adb import ADB
from .rpc import RPC
from .com import CSerial

class iAuto(Device):
    """iAuto 2.0 Device Class"""
    def __init__(self, serialno=None, host=('192.168.5.111', 5391), stream_method='STREAMSERVICE', auto_connect=1):
        super(iAuto, self).__init__()
        #self.serialno = serialno or '%s:%i'%(ip,port) or ADB().devices(state="device")[0][0]
        self.ip = host[0]
        self.port = host[1]
        self.stream_method = stream_method
        #self.adb = ADB(self.serialno)
        self.adb_instance = None
        self.rpc_instance = None
        self._display_info = ()
        self.frame_gen = None
        self.lock = threading.Lock()
        if int(auto_connect):
            self.connect()
    
    def __del__(self):
        self.disconnect()

    def connect(self):
        self.rpc()
    
    def disconnect(self):
        self.stop_stream()
    
    def adb(self):
        if self.adb_instance is None:
            try:
                self.adb_instance = ADB()
            except:
                CSerial().waitUntilDeviceOn()
                CSerial().startADBService()
                self.adb_instance = ADB()
            self.adb_instance.shell('mount -o remount rw /')
            self.adb_instance.shell('mount -o remount rw /system')
        return self.adb_instance
    
    def rpc(self):
        try:
            self.lock.acquire()
            if self.rpc_instance is None:
                self.rpc_instance = RPC((self.ip, int(self.port)))
                self.rpc_instance.wait_connected()
        finally:
            self.lock.release()
        return self.rpc_instance
    
    def get_stream(self):
        if self.stream_method.upper() == 'STREAMSERVICE':
            stream_func = self._get_stream_streamservice
        else:
            stream_func = self._get_stream_snapshot
        try:
            for frame in stream_func():
                yield frame
        except Exception as e:
            print(e)
            self.stop_stream()
            yield None
    
    def stop_stream(self):
        if self.frame_gen:
            self.frame_gen.send(0)
            self.frame_gen = None

    def _get_stream_snapshot(self):
        while 1:
            try:
                frame = self.snapshot()
                yield frame
            except:
                yield None
                break
    
    def _get_stream_streamservice(self):
        video = 'rtsp://192.168.5.111:8554/test'
        cap = cv2.VideoCapture(video)
        running = 1
        while running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                yield None
            else:
                cv2.waitKey(1)
                yield frame
        else:
            cap.release()
            yield None
    
    def get_frame_from_stream(self):
        frame_gen = self._get_stream_streamservice()
        frame = next(frame_gen)
        try:
            frame_gen.send(0)
        except (TypeError, StopIteration):
            # TypeError: can't send non-None value to a just-started generator
            pass
        return frame

    def snapshot(self, filename=None, mode='wldebug'):
        try:
            if mode == 'adb':
                self.screen = self.adb.snapshot()
            elif mode == 'streamservice':
                #import autost.device.video.stream
                #self.screen = autost.device.video.stream.snapshot()
                self.screen = self.get_frame_from_stream()
            else:# mode == 'wldebug':
                self.screen = self.rpc().call('snapshot')
                self.screen = base64.b64decode(self.screen)
                self.screen = aircv.utils.string_2_img(self.screen)
            
            if not self._display_info:
                self._display_info = self.screen.shape[:2][::-1]
            if filename:
                aircv.imwrite(filename, self.screen)
            return self.screen
        except Exception:
            #import traceback
            #traceback.print_exc()
            #return None
            raise
            
    def get_current_resolution(self):
        #return (1,1)
        if not self._display_info:
            self.snapshot(mode='wldebug_screen')
        return self._display_info
    
    def dump(self, onlyVisibleNode=True):
        data = self.rpc().call('dump')
#        print('=====================')
#        print(data)
#        print('=====================')
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
    
    def home(self, **kwargs):
        return self.keyevent(70)

    def touch(self, target, duration=0.01, **kwargs):
        if duration <= 0.2:
            args = (
                    #'TOUCH=press,%i,%i,relative,0,0' % (target[0], target[1]),
                    #'TPADPRESS=press,%i,%i,0,0' % (target[0], target[1]),
                    #'TPADPRESS=release,%i,%i,0,0' % (target[0], target[1]),
                    #'TOUCH=release,%i,%i,relative,0,0' % (target[0], target[1]),
                    'TOUCH=press,%i,%i' % (target[0], target[1]),
                    'TOUCH=release,%i,%i' % (target[0], target[1]),
                    #'SLEEP=1000',
                    )
            rst = self.rpc().call('autokey', *args)
        else:
            args1 = (
                    'TOUCH=press,%i,%i' % (target[0], target[1]),
                    'SLEEP=10',
                    'TOUCH=hold,%i,%i' % (target[0], target[1]),
                    'SLEEP=10',
                    'LONGPRESS=%i,%i' % (target[0], target[1]),
                    )
            args2 = (
                    'TOUCH=release,%i,%i' % (target[0], target[1]),
                    )
            rst = self.rpc().call('autokey', *args1)
            time.sleep(duration)
            rst = self.rpc().call('autokey', *args2)
        return rst
    
    def test(self):
        args = (
                'KEY=70',
                'SLEEP=500',
                
                'TOUCH=press,%i,%i,relative,0,0' % (131, 170),
                'TPADPRESS=press,%i,%i,0,0' % (131, 170),
                'TPADPRESS=release,%i,%i,0,0' % (131, 170),
                'TOUCH=release,%i,%i,relative,0,0' % (131, 170),
                'SLEEP=500',
                
#                 'TOUCH=press,%i,%i,relative,0,0' % (79, 114),
#                 'TPADPRESS=press,%i,%i,0,0' % (79, 114),
#                 'TPADPRESS=release,%i,%i,0,0' % (79, 114),
#                 'TOUCH=release,%i,%i,relative,0,0' % (79, 114),
#                 'SLEEP=1000',
#                 
#                 'TOUCH=press,%i,%i,relative,0,0' % (360, 167),
#                 'TPADPRESS=press,%i,%i,0,0' % (360, 167),
#                 'TPADPRESS=release,%i,%i,0,0' % (360, 167),
#                 'TOUCH=release,%i,%i,relative,0,0' % (360, 167),
#                 'SLEEP=1000',
                )
        rst = self.rpc().call('autokey', *args)
        return rst

    def swipe(self, t1, t2, **kwargs):
        args = (
                'TOUCH=press,%i,%i' % (t1[0], t1[1]),
                'SLEEP=20',
                'TOUCH=hold,%i,%i' % (t1[0], t1[1]),
                'SLEEP=20',
                'LONGPRESS=%i,%i' % (t1[0], t1[1]),
                'SLEEP=20',
                'TOUCH=move,%i,%i' % (t2[0], t2[1]),
                'SLEEP=20',
                'TOUCH=hold,%i,%i' % (t2[0], t2[1]),
                'SLEEP=20',
                'TOUCH=release,%i,%i' % (t2[0], t2[1]),
                )
        rst = self.rpc().call('autokey', *args)
        return rst
    
    def flick(self, pos, direction, speed='normal', **kwargs):
        dir1, dir2, mx, my = direction
        args = (
                'TOUCH=press,%i,%i' % (pos[0], pos[1]),
                'SLEEP=20',
                'TOUCH=hold,%i,%i' % (pos[0], pos[1]),
                'SLEEP=20',
                'TOUCH=move,%i,%i' % (pos[0]+mx, pos[1]+my),
                'SLEEP=20',
                'TOUCH=move,%i,%i' % (pos[0]+mx+mx, pos[1]+my+my),
                'SLEEP=20',
                'FLICK=%i,%i,%s,%s,%s' % (pos[0]+mx+mx, pos[1]+my+my, dir1, dir2, speed),
                'SLEEP=1',
                'TOUCH=release,%i,%i' % (pos[0]+mx+mx, pos[1]+my+my),
                )
        rst = self.rpc().call('autokey', *args)
        return rst
    
    def pinch(self, center, scale):
        x, y = center
        x1, y1 = x - 50, y - 50
        x2, y2 = x + 50, y + 50
        if scale > 1:
            mx1, my1 = x - 60, y - 60
            mx2, my2 = x + 60, y + 60
        else:
            mx1, my1 = x - 40, y - 40
            mx2, my2 = x + 40, y + 40
        
        args = (
                'TOUCH=press,%i,%i' % (x1, y1),
                'SLEEP=20',
                'TOUCH=hold,%i,%i' % (x1, y1),
                'SLEEP=20',
                'MULTITOUCH=hold,%i,%i,press,%i,%i' % (x1, y1, x2, y2),
                'SLEEP=20',
                'MULTITOUCH=hold,%i,%i,hold,%i,%i' % (x1, y1, x2, y2),
                'SLEEP=20',
                'MULTITOUCH=move,%i,%i,move,%i,%i' % (mx1, my1, mx2, my2),
                'SLEEP=20',
                'PINCH=%i,%i,%i' % (int(scale*100), x, y),
                'SLEEP=20',
                'MULTITOUCH=release,%i,%i,hold,%i,%i' % (mx1, my1, mx2, my2),
                'SLEEP=20',
                'TOUCH=release,%i,%i' % (mx2, my2),
                )
        rst = self.rpc().call('autokey', *args)
        return rst
    

    KEY_COLLECTIONS = {
        'HOME': 94,
        'MENU': 70,
        'AUDIO': 74,
        'MAP': 98,
        'SEEK': 23,
        'TRACK': 24,
        'PHONE': 86,
        'APPS': 97,
        'TUNE_UP': [768, 1],
        'TUNE_DOWN': [768, -1],
        'VOLUME_UP': [769, 1],
        'VOLUME_DOWN': [769, -1],
        'VOICE': 1286,
        }
    
    def keyevent(self, keyname, **kwargs):
        key = self.KEY_COLLECTIONS.get(keyname)
        if not key:
            raise KeyError
        if type(key) == type([]):
            key, step = key
            rst = self.rpc().call('autokey', 'ROTARYKEY=%s,%s' % (str(key), str(step)))
        else:
            rst = self.rpc().call('autokey', 'KEY=%s' % str(key))
        return rst
    
    def rotary_key(self, key, step, **kwargs):
        rst = self.rpc().call('autokey', 'ROTARYKEY=%s,%s' % (str(key), str(step)))
        return rst

    def text(self, text, enter=True):
        raise NotImplementedError
        
    def setup(self, project='17cyplus', machine='t2', area='uc'):
        print('auto setup...')
        adb = self.adb()
        iauto2_dir = os.path.sep.join([__file__[:__file__.rfind(os.path.sep)], 'env'])
        
        data_dirs = [
                    project,
                    '_'.join([project, machine]),
                    '_'.join([project, machine, area]),
                    ]
        for data_dir in data_dirs:
            src_data_dir = os.path.sep.join([iauto2_dir, data_dir])
            self._push_dir(adb, src_data_dir, '')
    
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

    def wake(self):
        CSerial().waitUntilDeviceOn()
        CSerial().startStreamService()
        #self.startStreamService()
        CSerial().startTestService()
        #self.startTestService()
    
    def startStreamService(self):
        adb = self.adb()
        adb.shell('cp /data/stream/* /lib/; sync')
        adb.shell('cd /lib; ./stream_so_link.sh', ignore="link failed File exists")
        adb.shell("export PATH=$PATH:/data/bin; killall streamservice", ignore="no process killed")
        adb.shell("export PATH=$PATH:/data/bin; killall Teststreamservice", ignore="no process killed")
        adb.shell('iptables -F')
        adb.shell('iptables -P INPUT ACCEPT')
        adb.shell('iptables -P OUTPUT ACCEPT')
        adb.cmd('streamservice &')
        adb.cmd('Teststreamservice &')
    
    def startTestService(self):
        adb = self.adb()
        adb.shell('/data/iauto2test &')
    
    def fetch_log(self, hu_log_path='/var/system', pc_log_path='./'):
        print('fetch dcu log...')
        adb = self.adb()
        adb.shell('export PATH=$PATH:/data/bin; tar -czvf /data/log_dcu.tar.gz /var/system')
        if not os.path.exists(pc_log_path):
            os.mkdir(pc_log_path)
        adb.pull('/data/log_dcu.tar.gz', pc_log_path)

G.register_custom_device(iAuto)

