from autost.api import *

keyevent(KEY_MENU)

touch(Template('audio.png'))

touch_if(Template('source.png'))

touch_or(Template('am_black.png'), Template('am_highlight.png'))

assert_exists(Template('am_screen_mark.png'))