# -*- coding: utf-8 -*-

import time
import sounddevice
import argparse
import logging
logging.disable(logging.DEBUG)

#from six.moves.urllib.parse import parse_qsl, urlparse
#from airtest.core.settings import Settings as ST
#from airtest.core.cv import Template, loop_find
#from airtest.core.error import TargetNotFoundError
#from airtest.core.helper import (G, delay_after_operation, import_device_cls, logwrap)
import airtest.core.api
from airtest import aircv
from airtest.core.error import DeviceConnectionError
from airtest.core.helper import G
from airtest.core.api import *

from autost.device.iauto2 import iAuto
from autost.device.android import iAndroid
from autost.device.poco import iAutoPoco
from autost.audio import stt
from autost.audio.audio_process import AudioProcess
import autost.hdbox
import autost.audio.cv


Template = autost.audio.cv.Template
loop_find = autost.audio.cv.loop_find
ST.THRESHOLD = 0.7
ST.THRESHOLD_PRECIOUS = 0.98
ST.OPDELAY = 0.2
G.DEVICE_URI = 'iauto://192.168.5.111:5391'


def connect_device(uri):
    dev = airtest.core.api.connect_device(uri)
    dev.uri = uri
    return dev

def disconnect_device(uri):
    for dev in G.DEVICE_LIST:
        if dev.uri == uri:
            G.DEVICE_LIST.remove(dev)
            if len(G.DEVICE_LIST) > 0:
                G.DEVICE = G.DEVICE_LIST[0]
            if hasattr(dev, 'disconnect'):
                dev.disconnect()

def device(uri=None):
    if uri is None:
        return G.DEVICE
    else:
        for dev in G.DEVICE_LIST:
            if dev.uri == uri:
                return dev

@logwrap
def switch_device(uri):
    for dev in G.DEVICE_LIST:
        if dev.uri == uri:
            G.DEVICE = dev
            #kwargs.pop('device')
            break
    else:
        raise RuntimeError("There is NOT connection to device %s..." % uri)

def device_selector(f):
    def func(*args, **kwargs):
        #
        old_dev = G.DEVICE
        
        #
        device_uri = kwargs.get('device')
        if device_uri:
            switch_device(device_uri)
        else:
            switch_device(G.DEVICE_LIST[0].uri)
        #
        try:
            f(*args, **kwargs)
        finally:
            G.DEVICE = old_dev
    return func

@logwrap
def bup_on(delay=0.0):
    autost.hdbox.bup_on()
    delay_after_operation(delay)

@logwrap
def bup_off(delay=0.0):
    autost.hdbox.bup_off()
    delay_after_operation(delay)

@logwrap
def acc_on(uri=G.DEVICE_URI, delay=30.0):
    autost.hdbox.acc_on()
    disconnect_device(uri)
    if delay:
        time.sleep(delay)
        wait_for_boot(uri)

def wait_for_boot(uri=G.DEVICE_URI, retry=30):
    for i in range(retry):
        try:
            d = urlparse(uri)
            cls = import_device_cls(d.scheme)
            cls.wait_for_boot()
            connect_device(uri)
            if G.DEVICE:
                disconnect_device(uri)
                break
        except RuntimeError:
            if i < retry:
                pass
            else:
                raise

@logwrap
def acc_off(delay=0.0):
    autost.hdbox.acc_off()
    delay_after_operation(delay)

def boot(uri=G.DEVICE_URI, **kwargs):
    autost.hdbox.bup_on()
    acc_on(uri, **kwargs)

@logwrap
def reboot(uri=G.DEVICE_URI, **kwargs):
    autost.hdbox.halt()
    time.sleep(1.0)
    autost.hdbox.bup_on()
    acc_on(uri, **kwargs)

def halt():
    autost.hdbox.halt()

@logwrap
def rev_on(delay=0.0):
    autost.hdbox.rev_on()
    delay_after_operation(delay)

@logwrap
def rev_off(delay=0.0):
    autost.hdbox.rev_off()
    delay_after_operation(delay)

@logwrap
def ig_on(delay=0.0):
    autost.hdbox.ig_on()
    delay_after_operation(delay)

@logwrap
def ig_off(delay=0.0):
    autost.hdbox.ig_off()
    delay_after_operation(delay)
    
@logwrap
def ill_on(delay=0.0):
    autost.hdbox.ill_on()
    delay_after_operation(delay)

@logwrap
def ill_off(delay=0.0):
    autost.hdbox.ill_off()
    delay_after_operation(delay)

@logwrap
def ill_down(hz, val, delay=0.0):
    """
    ill- control.

    :param hz:  scope [126-166]  --0x7E-0xA6
    :param val: scope [0-100]    --0x00-0x64
    """
    if (
        int(hz) < 126 or int(hz) > 166
        or
        int(val) < 0 or int(val) > 100
        ):
        raise RuntimeError("input param error...")
    else:
        autost.hdbox.ill_down(hz, val)
        delay_after_operation(delay)

@logwrap
def pkb_on(delay=0.0):
    autost.hdbox.pkb_on()
    delay_after_operation(delay)

@logwrap
def pkb_off(delay=0.0):
    autost.hdbox.pkb_off()
    delay_after_operation(delay)

@logwrap
def spd_speed(speed, delay=0.0):
    autost.hdbox.spd_speed(speed)
    delay_after_operation(delay)

@logwrap
def usb_on(port, delay=0.0):
    autost.hdbox.usb_on(port)
    delay_after_operation(delay)

@logwrap
def usb_off(port, delay=0.0):
    autost.hdbox.usb_off(port)
    delay_after_operation(delay)

KEY_HOME=HOME='HOME'
KEY_MENU=MENU='MENU'
KEY_AUDIO=AUDIO='AUDIO'
KEY_MAP=MAP='MAP'
KEY_SEEK=SEEK='SEEK'
KEY_TRACK=TRACK='TRACK'
KEY_PHONE=PHONE='PHONE'
KEY_APPS=APPS='APPS'
KEY_TUNE_UP=TUNE_UP='TUNE_UP'
KEY_TUNE_DOWN=TUNE_DOWN='TUNE_DOWN'
KEY_VOLUME_UP=VOLUME_UP='VOLUME_UP'
KEY_VOLUME_DOWN=VOLUME_DOWN='VOLUME_DOWN'
KEY_VOLUME_DOWN=VOLUME_DOWN='VOLUME_DOWN'
KEY_VOICE=VOICE='VOICE'

@device_selector
@logwrap
def keyevent(keyname, delay=ST.OPDELAY, **kwargs):
    """
    Perform key event on the device

    :param keyname: platform specific key name
    :param **kwargs: platform specific `kwargs`, please refer to corresponding docs
    """
    try:
        kwargs.pop('device')
    except:
        pass
    G.DEVICE.keyevent(keyname, **kwargs)
    delay_after_operation(delay)

@device_selector
@logwrap
def touch(v, inv=None, duration=0.01, delay=ST.OPDELAY, **kwargs):
    """
    Perform the touch action on the device screen

    :param v: target to touch, either a Template instance or absolute coordinates (x, y)
    :param inv: if not None, inv is the perdict area
    :param kwargs: platform specific `kwargs`, please refer to corresponding docs
    """
    try:
        kwargs.pop('device')
    except:
        pass
    if isinstance(v, Template):
        pos = loop_find(v, inv=inv, raise_error=True, **kwargs)
    else:
        try_log_screen()
        pos = v

    G.DEVICE.touch(pos, duration=duration, **kwargs)
    delay_after_operation(delay)

touch_in = touch

@device_selector
@logwrap
def touch_or(v, orv, delay=ST.OPDELAY, **kwargs):
    """
    Perform the touch action on the device screen

    :param v: target to touch, either a Template instance or absolute coordinates (x, y)
    :param orv: if not None, orv is the perdict area
    :param kwargs: platform specific `kwargs`, please refer to corresponding docs
    """
    try:
        kwargs.pop('device')
    except:
        pass
    if isinstance(v, Template):
        pos = loop_find(v, orv=orv, raise_error=True, **kwargs)
#         try:
#             pos = _exists(v, orv, raise_error = True, **kwargs)
#         except TargetNotFoundError:
#             screen = None
#             if hasattr(device(), 'screen'):
#                 screen = device().screen
#             try_log_screen(screen)
#             raise
#         except:
#             raise
    else:
        try_log_screen()
        pos = v

    G.DEVICE.touch(pos, **kwargs)
    delay_after_operation(delay)

@device_selector
@logwrap
def touch_if(v, delay=ST.OPDELAY, **kwargs):
    try:
        kwargs.pop('device')
    except:
        pass
    if isinstance(v, Template):
        pos = loop_find(v, raise_error=False, **kwargs)
    else:
        try_log_screen()
        pos = v
    
    if pos:
        G.DEVICE.touch(pos, **kwargs)
        delay_after_operation(delay)

@device_selector
@logwrap
def long_touch(v, inv=None, duration=2.0, delay=ST.OPDELAY, **kwargs):
    """
    Perform the touch action on the device screen

    :param v: target to touch, either a Template instance or absolute coordinates (x, y)
    :param inv: if not None, inv is the perdict area
    :param kwargs: platform specific `kwargs`, please refer to corresponding docs
    """
    try:
        kwargs.pop('device')
    except:
        pass
    if isinstance(v, Template):
        pos = loop_find(v, inv=inv, raise_error=True, **kwargs)
    else:
        try_log_screen()
        pos = v

    G.DEVICE.touch(pos, duration=duration, **kwargs)
    delay_after_operation(delay)

@device_selector
@logwrap
def swipe(v1, v2=None, vector=None, delay=ST.OPDELAY, deviation=5, **kwargs):
    """
    Perform the swipe action on the device screen.

    There are two ways of assigning the parameters
        * ``swipe(v1, v2=Template(...))``   # swipe from v1 to v2
        * ``swipe(v1, vector=(x, y))``      # swipe starts at v1 and moves along the vector.
    
    :param deviation: to avoid deviation, add 5-dot onto the movement
    """
    if isinstance(v1, Template):
        pos1 = loop_find(v1, timeout=ST.FIND_TIMEOUT)
    else:
        try_log_screen()
        pos1 = v1

    if v2:
        if isinstance(v2, Template):
            pos2 = loop_find(v2, timeout=ST.FIND_TIMEOUT_TMP)
        else:
            pos2 = v2
        vector = (pos2[0] - pos1[0], pos2[1] - pos1[1])
    
    if vector:
        x2, y2 = pos1[0] + vector[0], pos1[1] + vector[1]
        
        # deviation
        if deviation:
            if vector[0] > 5:
                x2 = x2 + 5
            elif vector[0] < -5:
                x2 = x2 - 5
            
            if vector[1] > 5:
                y2 = y2 + 5
            elif vector[1] < -5:
                y2 = y2 - 5
            
        # ensure legal coordinate
        w, h = G.DEVICE.get_current_resolution()
        if x2 < 0:
            x2 = 0
        if x2 > w:
            x2 = w
        if y2 < 0:
            y2 = 0
        if y2 > h:
            y2 = h
        
        #
        pos2 = (x2, y2)
    else:
        raise Exception("no enough params for swipe")

    G.DEVICE.swipe(pos1, pos2)
    delay_after_operation(delay)


DIR_UP=('up','up', 1, -10)
DIR_DOWN=('down','down', 1, 10)
DIR_LEFT=('left','left', 10, 1)
DIR_RIGHT=('right','right', -10, 1)
DIR_UP_LEFT=('up','top left', 10, -10)
DIR_UP_RIGHT=('up','top right', -10, -10)
DIR_DOWN_LEFT=('down','bottom left', 10, 10)
DIR_DOWN_RIGHT=('down','bottom right', -10, 10)
SPEED_NORMAL='normal'
SPEED_SLOW='slow'
SPEED_FAST='fast'

@device_selector
@logwrap
def flick(v, direction, step=1, speed=SPEED_NORMAL, delay=ST.OPDELAY, **kwargs):
    """
    Perform the flick action on the device screen.
    """
    #
    if isinstance(v, Template):
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT)
    else:
        try_log_screen()
        pos = v
    
    #
    if step > 1:
        dir1, dir2, mx, my = direction
        if abs(mx) > 1:
            mx = int(mx * step)
        if abs(my) > 1:
            my = int(my * step)
        direction = dir1, dir2, mx, my
    
    #
    G.DEVICE.flick(pos, direction, speed)
    delay_after_operation(delay)

@device_selector
@logwrap
def pinch(center=None, scale=0.5, delay=ST.OPDELAY, **kwargs):
    """
    Perform the pinch action on the device screen

    :param center: center of pinch action, default as None which is the center of the screen
    :param scale: percentage of the screen of pinch action, default is 0.5
    """
    G.DEVICE.pinch(center=center, scale=scale)
    delay_after_operation(delay)

@device_selector
@logwrap
def exists(v, inv=None, timeout=ST.FIND_TIMEOUT, msg='', raise_error=False, **kwargs):
    return loop_find(v, inv=inv, timeout=timeout, raise_error=raise_error)

@device_selector
@logwrap
def assert_exists(v, inv=None, timeout=ST.FIND_TIMEOUT, msg='', **kwargs):
    """
    Assert target exists on device screen

    :param v: target to be checked
    :param inv: if not None, inv is the perdict area
    :param msg: short description of assertion, it will be recorded in the report
    :raise AssertionError: if assertion fails
    :return: coordinates of the target
    """
    try:
        if v.threshold < ST.THRESHOLD_PRECIOUS:
            v.threshold = ST.THRESHOLD_PRECIOUS
        pos = loop_find(v, inv=inv, timeout=timeout, raise_error=True)
        return pos
    except TargetNotFoundError:
        raise AssertionError("%s does not exist in screen, message: %s" % (v, msg))

@device_selector
@logwrap
def assert_not_exists(v, timeout=ST.FIND_TIMEOUT, msg="", **kwargs):
    try:
        pos = loop_find(v, timeout=timeout)
        raise AssertionError("%s exists unexpectedly at pos: %s, message: %s" % (v, pos, msg))
    except TargetNotFoundError:
        pass

@device_selector
@logwrap
def wait(v, inv=None, timeout=3.0, interval=0.5, msg='', raise_error=False, **kwargs):
    start = time.time()
    while True:
        start_loop = time.time()
        pos = loop_find(v, inv=inv, timeout=interval, raise_error=raise_error)
        if time.time() - start_loop < interval:
            time.sleep(time.time() - start_loop)
        if pos:
            break
        if time.time() - start > timeout:
            raise AssertionError("%s still exists unexpectedly at pos: %s, message: %s" % (v, pos, msg))

wait_for_appearence = wait

@device_selector
@logwrap
def wait_for_disappearence(v, inv=None, timeout=3.0, interval=0.5, msg='', raise_error=False, **kwargs):
    start = time.time()
    while True:
        start_loop = time.time()
        pos = loop_find(v, inv=inv, timeout=interval, raise_error=raise_error)
        if time.time() - start_loop < interval:
            time.sleep(time.time() - start_loop)
        if not pos:
            break
        if time.time() - start > timeout:
            raise AssertionError("%s still exists unexpectedly at pos: %s, message: %s" % (v, pos, msg))

def delay_after_operation(delay=ST.OPDELAY):
    time.sleep(delay)

def poco(name=None, **kw):
    poco_handle = iAutoPoco.instance()
    return poco_handle(name, **kw)

@logwrap
def hears(words):
    try:
        stt.loop_hear(words, timeout=ST.FIND_TIMEOUT_TMP)
    except TargetNotFoundError:
        return False
    else:
        return True

@logwrap
def assert_hears(words):
    try:
        stt.loop_hear(words, timeout=ST.FIND_TIMEOUT)
        return True
    except TargetNotFoundError:
        raise AssertionError("words have not been heared yet, words: %s" % (words))


sound = ''

def start_listen():
    fs = 44100 # Hz
    length = 100 # s
    global sound
    try:
        sound = sounddevice.rec(frames=fs * length, samplerate=fs, channels=1)
    except:
        pass

def stop_listen():
    sounddevice.stop()


audio_process = AudioProcess()

@logwrap
def play_file(filename):
    """
    Perform key event on the device

    :param keyname: platform specific key name
    :param **kwargs: platform specific `kwargs`, please refer to corresponding docs
    """

    global audio_process

    
    #print(filename)
    audio_process.auto_test_play_file(filename)
    
    #delay_after_operation(delay)

@logwrap
def match_record(filename):
    global audio_process
    print(filename)

    audio_process.auto_test_match_record(filename)

@logwrap
def start_audio_test(case_dir):
    global audio_process        
    audio_process.start_audio_test(case_dir)    
    

@logwrap
def stop_audio_test():
    global audio_process    
    audio_process.stop_audio_test()   


@logwrap
def start_siri(case_dir):
    global audio_process
    audio_process.start_siri(case_dir)
    pass

@logwrap
def stop_siri():
    global audio_process
    case_list = audio_process.stop_siri()    
    return case_list


@logwrap
def start_record(case_dir,case_call_back=None):
    global audio_process
    case_list = audio_process.start_record(case_dir,None,case_call_back)    
    return case_list     

def start_play_file_list(filename,case_call_back):
    global audio_process
    
    case_dir,_ = os.path.split(filename)
    case_list = audio_process.start_record(case_dir,filename,case_call_back)    
    return case_list     

@logwrap
def play_wave_file(filename):
    global audio_process
    case_list = audio_process.play_wave_file(filename)    
    return case_list    


@logwrap
def stop_record():
    global audio_process
    case_list = audio_process.stop_record()    
    return case_list    