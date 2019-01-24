# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-7-27

@author: wushengbing
'''


def trace(f):
    def func(*args, **kwargs):
        try:
            try:
                r = f(*args, **kwargs)
            except:
                r = f(args[0])
        except:
            import traceback
            print('function : %s' % f)
            print(traceback.print_exc())
            return None
        return r
    return func