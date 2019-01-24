from autost.api import *

usb_on(1)
keyevent(KEY_MENU)
touch(Template('display.png'))
touch(Template('general.png'))
long_touch(Template('left.png'), duration=5.0)
long_touch(Template('right.png'), duration=5.0)

for _ in range(2):
    long_touch(Template('TBTN1.png'), duration=3.0)
    touch(Template('keyboard.png'))
    touch(Template('key.png'))
    for _ in range(3):
        touch(Template('8.png'))
        touch(Template('6.png'))

    touch(Template('OK.png'))
    long_touch(Template('TBTN2.png', threshold=0.99), duration=5.0)
    if exists(Template('ALLLOG.png')):
        break

touch(Template('ALLLOG.png'))
touch(Template('COPY2USB.png'))
sleep(3.0)
wait(Template('COPY2USB.png'))
touch(Template('dellog.png'))