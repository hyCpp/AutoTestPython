from autost.api import *

keyevent(KEY_MENU)

touch(Template('audio.png'))

rev_on()

assert_not_exists(Template('radio.png'))

rev_off()

assert_exists(Template('radio.png'))