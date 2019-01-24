# -*- coding: utf-8 -*-
import os
import time
import json
from collections import namedtuple
from airtest import aircv
from airtest.utils.transform import TargetPos
from airtest.aircv import cv2
from airtest.core.cv import Template
from airtest.core.helper import G, logwrap, log_in_func
from airtest.core.settings import Settings as ST

Rect = namedtuple('rect', ['x_min', 'x_max', 'y_min', 'y_max'])


def auto_focus(screen):
    if not os.path.exists(videoCapture.auto_focus()):
        raise RuntimeError('auto focus failed ! !')


def get_stream():
    cap = videoCapture()
    return cap.get_stream()


class CTemplate(Template):
    def __init__(self, filename, resolution=(), threshold=None, point=None, widget_rect=None):
        super(CTemplate, self).__init__(filename, resolution=resolution, threshold=threshold)

    def match_in(self, screen):
        match_result = self._cv_match(screen)
        G.LOGGING.debug("match result: %s", match_result)
        log_in_func({"cv": match_result})
        if not match_result:
            return None
        focus_pos = TargetPos().getXY(match_result, self.target_pos)
        match_result['focus_pos'] = focus_pos
        return match_result


class videoCapture(object):
    """
    #1. 获取视频流
    #2. 获取截屏有效区域基准位置
    #3. 调整有效区域（拉伸等）返回有效区域图片流
    """
    mCap = cv2.VideoCapture(0)
    confPath = os.path.join(os.getcwd(), 'camera_param.json')

    def __init__(self, conf=None, cap=None, predict_area=None, device=None, mode=None):
        """ device = cv2.VideoCapture"""
        self.conf_file = conf if conf else videoCapture.confPath
        self.capture = cap if cap else videoCapture.mCap
        self.conf = dict()
        self.mode = mode
        self.initialize()

    def initialize(self):
        try:
            self.conf = json.load(open(self.conf_file, 'r'))
        except:
            raise RuntimeError('Load camera config failed !')

    @classmethod
    def auto_focus(cls, screen, confPath=None):
        """ screen is shared in multi processing """
        screenPath = os.path.join(os.getcwd(), 'template.jpg')
        cv2.imwrite(screenPath, screen)
        screenTemplate = CTemplate(screenPath)
        """获取摄像头图像的匹配区域并保存至文件"""
        camera_conf = dict()
        videoCapture.mCap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        videoCapture.mCap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        ret = False
        while(not ret):
            ret, frame = videoCapture.mCap.read()
        match_result = screenTemplate.match_in(frame)
        rect_area = match_result.get('rectangle')
        camera_conf['rect'] = Rect(rect_area[0][1], rect_area[2][1], rect_area[0][0], rect_area[2][0])
        camera_conf['resolution'] = aircv.get_resolution(screen)
        with open(os.path.join(os.getcwd(), 'camera_param.json'), 'w') as conf:
            conf.seek(0)
            conf.truncate()
            json.dump(camera_conf, conf)
            if not confPath:
                confPath = os.path.join(os.getcwd(), 'camera_param.json')
            videoCapture.confPath = confPath
        return videoCapture.confPath

    def _get_roiRect(self, frame):
        """1.截取; 2.缩放 ; 3.镜像"""
        rect = self.conf.get('rect')
        resolution = self.conf.get('resolution')
        roi_rect = Rect(rect[0], rect[1], rect[2], rect[3])
        roi_frame = frame[roi_rect.x_min:roi_rect.x_max, roi_rect.y_min:roi_rect.y_max]
        roi_frame = cv2.resize(roi_frame, tuple(resolution), interpolation=cv2.INTER_CUBIC)
        roi_frame = cv2.flip(roi_frame, 1) if self.mode == 'flip' else roi_frame
        return roi_frame

    def get_stream(self):
        """ """
        while(1):
            ret, frame = videoCapture.mCap.read()
            stime = time.time()
            while(not ret):
                if(time.time() - stime) > 10:
                    raise RuntimeError('videoCaputure read time out. please check videoCapture!')
                ret, frame = videoCapture.cap.read()
            roi_rect = self._get_roiRect(frame)
            yield roi_rect


"""unit test"""
if __name__ == "__main__":
    conf_path = videoCapture.auto_focus((cv2.VideoCapture(0).read())[1])
    cap = videoCapture(conf_path)
    while(True):
        cv2.imshow('capture', next(cap.get_stream()))
        cv2.waitKey(1)
    print('Done')
