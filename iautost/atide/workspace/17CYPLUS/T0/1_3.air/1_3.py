from autost.api import *

keyevent(KEY_MENU)

touch(Template('audio.png'))

touch_if(Template('source.png'))

touch_if(Template('bt_black.png'))

assert_exists(Template('bt_add_dialog.png'))