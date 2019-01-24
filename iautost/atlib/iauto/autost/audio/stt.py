# -*- coding: utf-8 -*-

import time

from airtest.core.helper import G, logwrap
from airtest.core.settings import Settings as ST
from airtest.core.error import TargetNotFoundError


def loop_hear(words, timeout=ST.FIND_TIMEOUT_TMP):
    G.LOGGING.info("Try listenning:\n%s", words)
    start_time = time.time()
    from pocketsphinx import LiveSpeech
    for x in LiveSpeech():
        G.LOGGING.info('hearing word: %s', str(x))
        if str(x) in words:
            return True
        if (time.time() - start_time) > timeout:
            raise TargetNotFoundError('Words %s not heared' % words)