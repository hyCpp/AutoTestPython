from autost.api import *

#touch(Template('Sound.png'))
poco = iAutoPoco()
poco(text='Sound').click()

touch(Template('TMB.png'))

touch_in(Template('up.png'), Template('Bass.png'))

assert_exists(Template('Bass_right.png'))

touch_in(Template('down.png'), Template('Bass_right.png'))

assert_exists(Template('Bass.png'))