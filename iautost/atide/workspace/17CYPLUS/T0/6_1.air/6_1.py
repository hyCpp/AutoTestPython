from autost.api import *

keyevent(KEY_VOLUME_UP)

assert_exists(Template('vol_change.png'))