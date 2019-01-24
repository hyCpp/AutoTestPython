from autost.api import *

touch(Template('Sound.png'))

touch(Template('TMB.png'))

touch_in(Template('up.png'), Template('Mid.png'))
assert_exists(Template('Mid_right.png'))

touch_in(Template('down.png'), Template('Mid.png'))
assert_exists(Template('Mid.png'))