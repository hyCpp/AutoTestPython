from autost.api import *

keyevent(KEY_MENU)

touch(Template('audio.png'))

touch_if(Template('source.png'))
#source_pos = exists(Template('source.png'))
#if source_pos:
#    touch(source_pos)

touch_or(Template('fm_black.png'), Template('fm_highlight.png'))
#fm_black = exists(Template('fm_black.png'))
#if fm_black:
#    touch(fm_black)
#else:
#    touch(Template('fm_highlight.png'))