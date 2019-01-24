# -*- coding: utf-8 -*-
import sys
import time
import datetime
import os
import math
import cv2
import threading
import PyQt5.QtWidgets
import PyQt5.QtGui
import PyQt5.QtCore
from autost.api import *
from ui import deviceController
from airtest.core.error import DeviceConnectionError

def record(f):
    def getFunction(args):
        func_list = []
        try:
            paras = args[1:]
        except:
            paras = []
        func_list.append((0, f.__name__ + '('))
        if f.__name__ == 'pinch':
            func_list.append((0, 'scale=%s)%s' % (paras[-1], os.linesep)))
            return func_list
        for p in paras:
            if isinstance(p, CTemplate):
                if p.template:
                    filename = p.template.filename
                    filename = filename[filename.rfind(os.sep)+1:]
                    file_dir = deviceController.REC.ASST.getCurrentEditorCaseDir()
                    func_list.append((1, os.path.join(file_dir,filename)))
                    continue
                else:
                    p = p.point
            p = str(p)
            if f.__name__ == 'flick':
                para_dict = {"('up', 'up', 1, -10)": "DIR_UP",
                             "('down', 'down', 1, 10)": "DIR_DOWN",
                             "('left', 'left', 10, 1)": "DIR_LEFT",
                             "('right', 'right', -10, 1)": "DIR_RIGHT",
                             "('up', 'top left', 10, -10)": "DIR_UP_LEFT",
                             "('up', 'top right', -10, -10)": "DIR_UP_RIGHT",
                             "('down', 'bottom left', 10, 10)": "DIR_DOWN_LEFT",
                             "('down', 'bottom right', -10, 10)": "DIR_DOWN_RIGHT",
                             }
                for k, v in para_dict.items():
                    p = p.replace(k, v)
            func_list.append((0, p))
        if f.__name__ == 'flick':
            func_list.append((0, "step=1, speed=SPEED_NORMAL"))
        elif f.__name__ == 'swipe':
            func_list.append((0, "deviation=5"))
        else:
            pass
        if deviceController.REC.DEVICE_NUM > 1:
             current_uri = deviceController.REC.DEVICE_URI
             if current_uri:
                 func_list.append((0,", device=%s)" % deviceController.REC.DEVICE_URI_MAPPING.get(current_uri) + os.linesep))
             else:
                 func_list.append((0,')' + os.linesep))
        else:
            func_list.append((0,')' + os.linesep))
        #func_list.append((0,')' + os.linesep))
        return func_list

    def func(*args):
        try:
            #
            if deviceController.REC.FLAG:
                func_list = getFunction(args)
                for i in range(len(func_list)):
                    k, v = func_list[i]
                    if k == 0:
                        deviceController.REC.ASST.insertText(v)
                    elif k == 1:
                        deviceController.REC.ASST.insertImage(v)
                    else:
                        pass
                    if i > 0 and i < len(func_list) - 2:
                        deviceController.REC.ASST.insertText(", ")
                try:
                    deviceController.REC.ASST.parent.editor.currentWidget().moveScrollToEnd()
                except:
                    pass
            #
            try:
                import threading
                t = threading.Thread(target=f, args=args)
                t.start()
                #r = f(*args)
            except TouchAmbiguousError as e:
                print(e.message)
                return
            except:
                f(args[0])
        except:
            import traceback
            print(traceback.print_exc())
            return None
        #return r
    return func


class TouchAmbiguousError(Exception):
    def __init__(self, msg):
        super(TouchAmbiguousError, self).__init__()
        self.message = msg


class CTemplate(object):
    """
     a new airtest.core.cv.Template
    """
    def __init__(self, point=None, template=None, widget_rect=None):
        self.point = point
        self.template = template
        self.widget_rect = widget_rect


class CLabel(PyQt5.QtWidgets.QLabel):
    def __init__(self, parent=None):
        super(CLabel, self).__init__(parent)
        self.parent = parent
        self.widget_flag = False
        self.setMouseTracking(True)
        self.widget_rect = [0, 0, 0, 0]
        self.widget_org_rect = [0, 0, 0, 0]
        self.move_time = 0
        self.press_time = 0
        self.widget_find_flag = False
        self.ctrl_alt_flag = 0

    def paintEvent(self, event):
        PyQt5.QtWidgets.QLabel.paintEvent(self, event)
        try:
            self.painter = PyQt5.QtGui.QPainter()
            self.painter.begin(self)
            self.painter.setBrush(PyQt5.QtGui.QColor(0, 255, 0, 50))
            self.painter.setPen(PyQt5.QtGui.QColor(255, 0, 255))
            if deviceController.REC.FLAG:
                self.painter.setPen(PyQt5.QtGui.QColor(0, 255, 0))
            x, y, w, h = self.widget_rect
            if w and h:
                self.painter.drawRect(x, y, w, h)
            self.painter.end()
        except:
            import traceback
            traceback.print_exc()

    def setRect(self, rect):
        self.widget_rect = rect

    def getWidgetTreeDataFlag(self):
        widget_tree_data_flag = False
        if hasattr(self.parent, 'device_proxy'):
            widget_tree_data_flag = self.parent.device_proxy.widget_tree_data_flag
        return widget_tree_data_flag

    def mousePressEvent (self, event):
        if event.button() == PyQt5.QtCore.Qt.RightButton:
            self.parent.hideWidget()
        elif event.button() == PyQt5.QtCore.Qt.LeftButton:
            self.widget_flag = False
            self.press_time = time.perf_counter()
            self.press_x, self.press_y =  event.x(), event.y()
        else:
            self.widget_flag = True

    def mouseMoveEvent(self, event):
        self.move_x, self.move_y = event.x(), event.y()
        if self.move_time == 0 and self.press_time != 0:
            self.move_time = time.perf_counter()
        if self.ctrl_alt_flag == 3 or self.ctrl_alt_flag == 1 and not self.getWidgetTreeDataFlag():
            if self.move_time != 0:
                rect = [self.press_x,
                        self.press_y,
                        self.move_x - self.press_x,
                        self.move_y - self.press_y]
                self.setRect(rect)
                self.repaint()
        else:
            if self.widget_flag or deviceController.REC.FLAG:
                self.parent.widgetShow.emit(self.move_x, self.move_y)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            scale = 2
        else:
            scale = 0.5
        self.pinch(None, scale)

    def mouseReleaseEvent (self, event):
        if event.button() != PyQt5.QtCore.Qt.LeftButton:
            return
        self.release_time = time.perf_counter()
        self.release_x, self.release_y = event.x(), event.y()
        if self.ctrl_alt_flag == 3 or self.ctrl_alt_flag == 1 and not self.getWidgetTreeDataFlag():
            org_rect = self.convertToOrgRect(self.widget_rect)
            if org_rect:
                capture_file = self.capture(org_rect)
                x, y, w, h = org_rect
                point = (x + w // 2, y + h // 2)
                v = CTemplate(template=Template(capture_file),
                              point=point,
                              widget_rect = org_rect)
                if self.ctrl_alt_flag == 3:
                    self.assert_exists(v)
                if self.ctrl_alt_flag == 1:
                    self.touch(v)
                self.parent.hideWidget()
        else:
            if not self.widget_find_flag:
                if (self.release_x, self.release_y) == (self.press_x, self.press_y):
                    v = self.point2widget((self.press_x, self.press_y))
                    if self.ctrl_alt_flag == 2:
                        if isinstance(v.template, Template):
                            self.assert_exists(v)
                        else:
                            print('assert_exists: template not exists...')
                    else:
                        interval_time = self.release_time - self.press_time
                        if interval_time > 2:
                            self.long_touch(v)
                        else:
                            self.touch(v)
                elif (self.release_x, self.release_y) == (self.move_x, self.move_y):
                    s_point = (self.press_x, self.press_y)
                    e_point = (self.move_x, self.move_y)
                    interval_time = self.move_time - self.press_time
                    if s_point and e_point:
                        if interval_time > 0.5:
                            self.swipe(self.point2widget(s_point), self.point2widget(e_point))
                        else:
                            direction = self.getFlickDirection(s_point, e_point)
                            self.flick(self.point2widget(s_point), direction)
                else:
                    pass
        self.move_time = 0
        self.press_time = 0

    def mapToScreen(self, point):
        pixmap = self.parent.pixmap
        pixmap_size = (pixmap.width(), pixmap.height())
        x, y = point
        scale = self.parent.getScale()
        x, y = list(map(lambda x: int(x / scale), [x, y]))
        if x >=0 and x < pixmap_size[0] and y >=0 and y < pixmap_size[1]:
            return [x, y]
        else:
            return None

    def getFlickDirection(self, s_point, e_point):
        vector = (e_point[0] - s_point[0], e_point[1] - s_point[1])
        angle = math.atan2(vector[1],vector[0])/math.pi*180
        if angle < 0:
            angle = 360 + angle
        angle_region = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5, 360]
        direction_list = [DIR_RIGHT, DIR_DOWN_RIGHT, DIR_DOWN, DIR_DOWN_LEFT,
                          DIR_LEFT, DIR_UP_LEFT, DIR_UP, DIR_UP_RIGHT, DIR_RIGHT]
        for i in range(len(angle_region)):
            if angle < angle_region[i]:
                break
        direction = direction_list[i]
        return direction

    def touch_event(self, v):
        flag = True
        if v.template:
            target_point = loop_find(v.template)
            if not self.isPointInWidget(v.widget_rect, target_point):
                parent_v = self.point2widget(v.point, find_parent=True)
                if parent_v.template:
                    flag = False
                    self.touch_in(v, parent_v, device=deviceController.REC.DEVICE_URI)
        if flag:
            self.touch(v, device=deviceController.REC.DEVICE_URI)

    @record
    def touch(self, v):
        try:
            touch(v.point, device=deviceController.REC.DEVICE_URI)
            print('touch :', v.point)
        except:
            pass

    @record
    def touch_in(self, v1, v2):
        try:
            touch(v1.point, device=deviceController.REC.DEVICE_URI)
            print('touch_in :', v1.template, v2.template)
        except:
            pass

    @record
    def long_touch(self, v):
        try:
            long_touch(v.point, device=deviceController.REC.DEVICE_URI)
            print('long_touch :', v.point)
        except:
            pass

    @record
    def swipe(self, v1, v2):
        try:
            swipe(v1.point, v2.point, device=deviceController.REC.DEVICE_URI)
            print('swipe :', v1.point, v2.point)
        except:
            pass

    @record
    def flick(self, v, direction):
        try:
            flick(v.point, direction, device=deviceController.REC.DEVICE_URI)
            print('flick :', v.point, direction)
        except:
            pass

    @record
    def pinch(self, center, scale):
        try:
            pinch(scale, device=deviceController.REC.DEVICE_URI)
            print('pinch :', scale)
        except:
            pass

    @record
    def assert_exists(self, v):
        print('assert_exists : ', v.template)

    def moveWidget(self, point):
        move_x, move_y = point
        try:
            x, y, w, h = self.widget_rect
        except:
            pass
        x1 = move_x - w/2
        y1 = move_y - h/2
        self.setRect([x1, y1, w, h])
        self.update()

    def findWidgetFromPoint(self, point):
        try:
            return deviceController.REC.ASST.parent.widgetTree.findWidgetFromPoint(point)
        except:
            return [None, None, None]

    def findWidgetParentFromPoint(self, point):
        try:
            return deviceController.REC.ASST.parent.widgetTree.findWidgetParentFromPoint(point)
        except:
            return [None, None, None]

    def getWidgetName(self, item):
        return deviceController.REC.ASST.parent.widgetTree.getWidgetCaptureName(item)

    def getCaseDir(self):
        try:
            return deviceController.REC.ASST.getCurrentEditorCaseDir()
        except:
            return None
    
    def convertToOrgRect(self, rect):
        x, y, w, h = rect
        p1 = self.mapToScreen((x, y))
        p2 = self.mapToScreen((x + w, y+h))
        if p1 and p2:
            x, y = p1
            w = p2[0] - x
            h = p2[1] - y
            return [x, y, w, h]
        return None

    def capture(self, org_rect, widget_name='capture'):
        x, y, w, h = org_rect
        pixmap = self.parent.pixmap.copy(x, y, w, h)
        capture_dir = self.getCaseDir()
        if not capture_dir:
            return None
        if os.path.exists(os.path.join(capture_dir, '%s.png' % widget_name)):
            widget_name += '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        capture_file = os.path.join(capture_dir, '%s.png' % widget_name)
        pixmap.save(capture_file)
        return capture_file

    def captureWidget(self, point, find_parent=False):
        if not deviceController.REC.FLAG:
            return None, None
        if self.ctrl_alt_flag == 1:
            return None, None
        if find_parent:
            item, rect, org_rect = self.findWidgetParentFromPoint(point)
        else:
            item, rect, org_rect = self.findWidgetFromPoint(point)
        if not item:
            return None, None
        widget_name = self.getWidgetName(item)
        capture_file = self.capture(org_rect, widget_name)
        if capture_file:
            return capture_file, org_rect
        else:
            return None, None

    def point2widget(self, point, find_parent=False):
        p = self.mapToScreen(point)
        t = None
        rect = None
        capture_file, rect = self.captureWidget(point, find_parent)
        if capture_file:
            t = Template(capture_file)
        return CTemplate(p, t, rect)

    def isPointInWidget(self, widget_rect, point):
        x, y, w, h = widget_rect
        px, py = point
        if px >= x and px < x + w and py >= y and py < y + h:
            return True
        else:
            return False


class CDeviceScreenWindow(PyQt5.QtWidgets.QDockWidget):
    deviceToolbarUpdate = PyQt5.QtCore.pyqtSignal(list, list)
    deviceWidgetRectUpdate = PyQt5.QtCore.pyqtSignal()
    widgetShow = PyQt5.QtCore.pyqtSignal(int, int)
    zoomFactorUpdate = PyQt5.QtCore.pyqtSignal()
    deviceScreenUpdate = PyQt5.QtCore.pyqtSignal()
    deviceWidgetOrgRectUpdate = PyQt5.QtCore.pyqtSignal(list)

    def __init__(self, parent=None, index=0):
        super(CDeviceScreenWindow, self).__init__()
        self.parent = parent
#        self.device_index = index
        self.device = None
        self.device_uri = None
        self.initUI()
        self.resize(800,800)
    
    def connect_device(self, device_uri=''):
        self.device_proxy = CDeviceProxy(self, device_uri)
        self.device_proxy.start()
        
    def disconnect_device(self, device_uri=''):
        #self.device_proxy = CDeviceProxy(self, device_uri)
        if hasattr(self, 'device_proxy'):
            try:
                self.device_proxy.stop()
            except:
                pass
        self.device = None
        
    def initUI(self):
        self.setWindowTitle('My Device')
        self.setWindowFlags(PyQt5.QtCore.Qt.FramelessWindowHint)
        self.setMouseTracking(False)
#        self.screen = PyQt5.QtWidgets.QLabel(self)
        self.screen = CLabel(self)
        self.screen.move(PyQt5.QtCore.QPoint(0,20))
        self.screen.setScaledContents(True)
        
        self.deviceScreenUpdate.connect(self.onScreenUpdate)
        self.setScreen()
        self.adjustSize()
        self.setFeatures(PyQt5.QtWidgets.QDockWidget.NoDockWidgetFeatures)
        
    def resizeEvent(self, event):
        self.updateScreen()
        event.accept()
        self.deviceWidgetRectUpdate.emit()

    def setScreen(self, screenshot='ui/device/snapshot/black_screen.jpg'):
        self.frame = screenshot
        self.deviceScreenUpdate.emit()
    
    def onScreenUpdate(self):
        #
        if type(self.frame) == type(""):
            self.pixmap = PyQt5.QtGui.QPixmap(self.frame)
        else:
            #print('self.frame.shape =', self.frame.shape)
            #cv2.cvtColor(self.frame, cv2.CV_BGR2RGB, self.frame)
            qimage = PyQt5.QtGui.QImage(self.frame.data, 
                                        self.frame.shape[1], 
                                        self.frame.shape[0], 
                                        self.frame.strides[0], 
                                        PyQt5.QtGui.QImage.Format_RGB888)
            qimage = qimage.rgbSwapped()
            self.pixmap = PyQt5.QtGui.QPixmap.fromImage(qimage)
        
        #
        self.screen_ratio = self.pixmap.width() * 1.0 / self.pixmap.height()
        self.screen.setPixmap(self.pixmap)
        self.updateScreen()
        self.update()

    def updateScreen(self):
        height = self.height() - 20
        w1, h1 = height * self.screen_ratio, height
        w2, h2 = self.width(), self.width() / self.screen_ratio
        if w1 <= self.width():
            self.screen.resize(w1, h1)
        else:
            self.screen.resize(w2, h2)
        self.zoomFactorUpdate.emit()

    def getScale(self):
        w1, h1 = self.pixmap.width(), self.pixmap.height()
        w2, h2 = self.screen.width(), self.screen.height()
        return w2 * 1.0 / w1

    def hideWidget(self):
        self.screen.setRect([0,0,0,0])
        self.deviceWidgetOrgRectUpdate.emit([0,0,0,0])
        self.screen.repaint()
        self.screen.widget_flag = False
        self.screen.widget_find_flag = False
        self.deviceToolbarUpdate.emit(['Find Widget'], [True])
        if hasattr(self, 'device_proxy'):
            self.device_proxy.resume()


class CDeviceProxy(PyQt5.QtCore.QObject):
    widgetTreeUpdate = PyQt5.QtCore.pyqtSignal(dict)
    
    def __init__(self, window, device_uri=''):
        super(CDeviceProxy, self).__init__()
        self.window = window
#        self.WidgetTreeUpdate.connect(window.parent.widgetTreeWindow.updateTree)
        self.current_screen = 'ui/device/snapshot/current_screen.jpg'
        self.black_screen = 'ui/device/snapshot/black_screen.jpg'
        self.device_uri = device_uri
        self.auto_connect = True
        self.widget_tree_data_flag = False
        
    def start(self):
        #
        if not self.device_uri:
            from . import setting
            self.device_uri = setting.DEVICE_URI
        G.DEVICE_URI = self.device_uri
        
        #
        self.auto_connect = True
        self.auto_update = True
        
        #
        objThread = threading.Thread(target=self.connect)
        objThread.setDaemon(True)
        objThread.start()
        
        #
        self.frame = None
        #self.connect_screen()
        objThread = threading.Thread(target=self.connect_screen)
        objThread.setDaemon(True)
        objThread.start()
        
        #
        self.controls_dirty = True
        objThread = threading.Thread(target=self.connect_controls)
        objThread.setDaemon(True)
        objThread.start()
    
    def stop(self):
        self.auto_connect = False
        if self.device_uri:
            disconnect_device(self.device_uri)
            self.device_uri = None
            self.window.device = None
        self.window.setScreen(self.black_screen)
    
    def pause(self):
        self.auto_update = False
    
    def resume(self):
        self.auto_update = True

    def connect(self):
        nTryTime = 0
        while self.auto_connect:
            #
            if self.auto_update:
                try:
                    if not self.window.device:
                        if nTryTime == 0:
                            print('Connecting device %s...' % self.device_uri)
                        nTryTime += 1
                        self.window.device = connect_device(self.device_uri)
                        self.window.device_uri = self.device_uri
                        print('Connect device %s successfully.' % self.device_uri)
                        nTryTime = 0
                except RuntimeError as e:
                    if nTryTime == 0:
                        print(e)
                    time.sleep(1.0)
                except DeviceConnectionError as e:
                    if nTryTime == 0:
                        print(e)
                    time.sleep(1.0)
                except:
                    import traceback
                    traceback.print_exc()
                    
            #else:
            #    if device():
            #        disconnect_device()
            
            #
            time.sleep(0.2)
    
    def disconnect(self):
        print('Device %s disconnected.' % self.device_uri)
        disconnect_device(self.device_uri)
        self.window.device = None
    
    def connect_screen(self):
        #return self._connect_screen_snapshot()
        platform = self.get_device_platform()
        if platform in ('iauto_simulator','android_emulator'):
            self._connect_screen_snapshot()
        elif platform in ('iauto', 'iandroid'):
            self._connect_screen_streamservice()
        else:
            pass
    
    def _connect_screen_snapshot(self):
        self.start_time = time.time()
        self.frame_number = 0
        while self.auto_connect:
            try:
                if self.auto_update:
                    if self.window.device:
                        frame = self.window.device.snapshot()
                        self.receive_frame_handle(frame)
                        continue
                #else:
                #    if device():
                #        disconnect_device()
                time.sleep(0.2)
            except RuntimeError:
                self.receive_frame_handle(None)
                time.sleep(1.0)
            except DeviceConnectionError:
                self.receive_frame_handle(None)
                time.sleep(1.0)
            except:
                self.receive_frame_handle(None)
                time.sleep(1.0)
                import traceback
                traceback.print_exc()
        
    def _connect_screen_streamservice(self):
        self.start_time = time.time()
        self.frame_number = 0
        while self.auto_connect:
            #
            if self.window.device:
                for frame in self.window.device.get_stream():
                    if not self.auto_connect:
                        break
                    if not self.auto_update:
                        continue
                    self.receive_frame_handle(frame)
                else:
                    self.disconnect()
            #
            time.sleep(0.2)
    
    def receive_frame_handle(self, frame):
        if self.auto_connect and self.auto_update:
            if frame is None:
                self.window.setScreen(self.black_screen)

            else:
                self.frame_number += 1
                if self.frame_number == 5:
                    current_time = time.time()
                    #print('fps =', self.frame_number / (current_time - self.start_time))
                    self.start_time = current_time
                    self.frame_number = 0
                #frame_same_rate = 0
                frame_diff = (frame == self.frame)
                frame_same_rate = len(frame[frame_diff]) * 1.0 / frame.size
                if frame_same_rate < 0.999:
                    #print(frame_same_rate)
                    self.frame = frame
                    self.window.setScreen(self.frame)
                    self.controls_dirty = True

    def update_widget_tree_data_flag(self, hierarchy):
        flag = False
        if len(hierarchy) > 1:
            flag = True
        self.widget_tree_data_flag = flag

    def connect_controls(self):
        while 1:
            try:
                if self.auto_update:
                    if self.controls_dirty:
                        self.controls_dirty = False
                        if self.window.device:
                            if hasattr(self.window.device, 'dump'):
                                hierarchy = self.window.device.dump()
                                self.widgetTreeUpdate.emit(hierarchy)
                                self.update_widget_tree_data_flag(hierarchy)
#                else:
#                    if self.window.device:
#                        self.window.device = None
                time.sleep(0.2)
            except RuntimeError:
                time.sleep(1.0)
            except DeviceConnectionError:
                time.sleep(1.0)
            except:
                self.widgetTreeUpdate.emit({})
                time.sleep(1.0)
                import traceback
                traceback.print_exc()

    def get_device_platform(self):
        if self.device_uri.startswith('iauto'):
            device_platform = 'iauto'
            if self.device_uri.find('ip=127.0.0.1') > 0:
                device_platform = 'iauto_simulator'
        elif self.device_uri.startswith('Windows'):
            device_platform = 'windows'
        elif self.device_uri.startswith('iAndroid'):
            device_platform = 'iandroid'
            if self.device_uri.find('emulator') > 0:
                device_platform = 'android_emulator'
        else:
            print('Unknow device platform...')
            device_platform = None
        return device_platform

#    def run(self):
#        if not self.device_uri:
#            from . import setting
#            self.device_uri = setting.DEVICE_URI
#        G.DEVICE_URI = self.device_uri
#        while 1:
#            #
#            try:
#                if self.auto_update:
#                    #
#                    if not device():
#                        #try:
#                        #    wait_for_boot(self.device_uri)
#                        #except:
#                        #    pass
#                        connect_device(self.device_uri)
#                    #
#                    snapshot(self.current_screen)
#                    self.window.setScreen(self.current_screen)
#                    hierarchy = device().dump()
#                    self.widgetTreeUpdate.emit(hierarchy)
#                else:
#                    if device():
#                        disconnect_device()
#                #
#                time.sleep(0.3333333333333)
#            except RuntimeError:
#                self.window.setScreen(self.black_screen)
#                self.widgetTreeUpdate.emit({})
#                disconnect_device()
#                time.sleep(1.0)
#            except:
#                self.window.setScreen(self.black_screen)
#                self.widgetTreeUpdate.emit({})
#                disconnect_device()
#                time.sleep(1.0)
#                import traceback
#                traceback.print_exc()

def Do():
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    w = CDeviceScreenWindow()
    w.show()
    
    #
    sys.exit(app.exec_())
    
    
    
if __name__ == '__main__':
    Do()
