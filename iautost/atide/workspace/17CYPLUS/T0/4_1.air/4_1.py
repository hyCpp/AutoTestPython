from autost.api import *


touch(Template('Sound.png'))


touch(Template('Fader_Balance.png'))


touch(Template('L.png'))
assert_exists(Template('FB_left.png'))


touch(Template('R.png'))
assert_exists(Template('FB_center.png'))


touch(Template('Front.png'))
assert_exists(Template('FB_front.png'))

touch(Template('Rear.png'))
assert_exists(Template('FB_center.png'))