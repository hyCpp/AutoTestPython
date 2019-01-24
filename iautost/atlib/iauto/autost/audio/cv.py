# -*- coding: utf-8 -*-

import os
import time

import airtest.core.cv
from airtest.core.cv import *


@logwrap
def loop_find(v, inv=None, orv=None, timeout=ST.FIND_TIMEOUT, threshold=None, interval=0.5, intervalfunc=None, raise_error=True):
    """
    Search for image template in the screen until timeout

    Args:
        v: image template to be found in screenshot
        inv: image template of perdict area
        timeout: time interval how long to look for the image template
        threshold: default is None
        interval: sleep interval before next attempt to find the image template
        intervalfunc: function that is executed after unsuccessful attempt to find the image template

    Raises:
        TargetNotFoundError: when image template is not found in screenshot

    Returns:
        TargetNotFoundError if image template not found, otherwise returns the position where the image template has
        been found in screenshot

    """
    if not inv:
        G.LOGGING.info("Try finding: %s", v)
    else:
        G.LOGGING.info("Try finding: %s in %s", v, inv)
    if threshold is not None:
        if v:
            v.threshold = threshold
        if orv:
            orv.threshold = threshold
        if inv:
            inv.threshold = threshold
    start_time = time.time()
    while True:
        screen = G.DEVICE.snapshot(filename=None)

        if screen is None:
            G.LOGGING.warning("Screen is None, may be locked")
        else:
            perdict_area = None
            if inv:
                perdict_center = inv.match_in(screen)
                if not perdict_center:
                    perdict_area = None
                    #raise TargetNotFoundError('Picture %s not found in screen' % inv)
                else:
                    perdict_area = inv.get_area(perdict_center)
            
            if not (inv is not None and perdict_area is None):
                match_pos = v.match_in(screen, perdict_area)
                if match_pos:
                    try_log_screen(screen)
                    return match_pos
                
                if orv:
                    match_pos = orv.match_in(screen, perdict_area)
                    if match_pos:
                        try_log_screen(screen)
                        return match_pos
        
        if intervalfunc is not None:
            intervalfunc()

        if (time.time() - start_time) > timeout:
            try_log_screen(screen)
            if raise_error:
                raise TargetNotFoundError('Picture %s not found in screen' % v)
            else:
                break
        else:
            time.sleep(interval)

class Template(airtest.core.cv.Template):
    def __init__(self, filename, **kwargs):
        #filename = os.path.abspath(filename)
        super(Template, self).__init__(filename, **kwargs)
    
    def get_area(self, center_pos=None):
        image = self._imread()
        h, w = image.shape[:2]
        if not center_pos:
            offset_w, offset_h = 0, 0
        else:
            offset_w, offset_h = center_pos
            offset_w, offset_h = int(offset_w - w / 2), int(offset_h - h / 2)
        return (offset_h, offset_h + h, offset_w, offset_w + w)

    def match_in(self, screen, perdict_area=None):
        if not perdict_area:
            match_result = self._cv_match(screen)
        else:
            h1, h2, w1, w2 = perdict_area
            screen = screen[h1 : h2, w1 : w2]
            match_result = self._cv_match(screen)
            if match_result:
                match_result["result"] = (match_result["result"][0] + w1, match_result["result"][1] + h1)
                match_result['rectangle'] = (
                                             (match_result['rectangle'][0][0] + w1, match_result['rectangle'][0][1] + h1),
                                             (match_result['rectangle'][1][0] + w1, match_result['rectangle'][1][1] + h1),
                                             (match_result['rectangle'][2][0] + w1, match_result['rectangle'][2][1] + h1),
                                             (match_result['rectangle'][3][0] + w1, match_result['rectangle'][3][1] + h1),
                                             )
        
        G.LOGGING.debug("match result: %s", match_result)
        log_in_func({"cv": match_result})
        if not match_result:
            return None
        focus_pos = TargetPos().getXY(match_result, self.target_pos)
        return focus_pos
    
    def _cv_match(self, screen):
        try:
            match_result = super(Template, self)._cv_match(screen)
            return match_result
        except cv2.error as e:
            return None
