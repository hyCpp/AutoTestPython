from autost.api import *

keyevent(KEY_MENU)

touch(Template('audio.png'))


if exists(Template('source.png')):
    touch(Template('source.png'))

if exists(Template('fm_highlight.png')):
    touch(Template('fm_highlight.png'))
else:
    touch(Template('fm_black.png'))