from autost.api import *


keyevent(KEY_MENU)

touch(Template('app.png'))
sleep(2.0)

touch(Template('scout.png'), threshold=0.95)
touch_if(Template('ok.png'), timeout=3.0)
touch_if(Template('ok2.png'), timeout=3.0)


assert_exists(Template('updown.png'))



usb_off(4)

sleep(10.0)

touch_if(Template('ok3.png'), timeout=3.0)


usb_on(4)

sleep(5.0)

touch_if(Template('ok4.png'), timeout=2.0)
sleep(1.0)
touch_if(Template('ok4.png'), timeout=2.0)


assert_not_exists(Template('updown2.png'))