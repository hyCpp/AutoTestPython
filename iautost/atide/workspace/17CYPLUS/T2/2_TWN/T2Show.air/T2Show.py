from autost.api import *

keyevent(KEY_MENU)

touch(Template('audio.png'))

touch_if(Template('source.png'))

rev_on()

assert_not_exists(Template('mark.png'))

rev_off()

assert_exists(Template('mark.png'))