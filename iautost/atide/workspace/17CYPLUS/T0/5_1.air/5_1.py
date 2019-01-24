from autost.api import *

touch(Template('Sound.png'))
touch(Template('ASL.png'))
touch(Template('High.png'))
assert_exists(Template('High1.png'))


touch(Template('Mid.png'))
assert_exists(Template('Mid1.png'))

touch(Template('Low.png'))
assert_exists(Template('Low1.png'))

touch(Template('Off.png'))
assert_exists(Template('Off1.png'))