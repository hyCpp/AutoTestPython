from autost.api import *

touch(Template('s.png'), device='iauto://127.0.0.1:5391/?stream_method=snapshot')

touch(Template('h.png'), device='iAndroid://127.0.0.1:5037/?stream_method=minicap')

assert_exists(Template('l.png'), device='iauto://127.0.0.1:5391/?stream_method=snapshot')

assert_exists(Template('a.png'), device='iAndroid://127.0.0.1:5037/?stream_method=minicap')

