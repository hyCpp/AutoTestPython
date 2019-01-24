from autost.api import *

touch(Template('Sound.png'))

#touch(Template('TMB.png'))
poco(text='Treble/Mid/Bass').click()

touch_in(Template('up.png'), Template('Treble.png'))
assert_exists(Template('Treble_right.png'))

touch_in(Template('down.png'), Template('Treble.png'))
assert_exists(Template('Treble.png'))