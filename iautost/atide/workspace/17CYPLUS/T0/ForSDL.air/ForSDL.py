from autost.api import *

keyevent(KEY_MENU)

touch(Template('App.png'))

touch(Template('Yelp.png'))

sleep(2.0)

touch(Template('Restaurants.png'))

sleep(3.0)

touch(Template('First.png'))

sleep(2.0)

touch(Template('touchmap.png'))


sleep(10.0)

touch(Template('go.png'))


sleep(4.0)

touch(Template('continue.png'))

assert_exists(Template('zoom in.png'))