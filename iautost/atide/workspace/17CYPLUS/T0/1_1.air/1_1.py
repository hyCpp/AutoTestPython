from autost.api import *

keyevent(KEY_MENU)

touch(Template('audio.png'))

touch_if(Template('source.png'))

touch_or(Template('fm_black.png'), Template('fm_highlight.png'))

assert_exists(Template('fm_screen_mark.png'))