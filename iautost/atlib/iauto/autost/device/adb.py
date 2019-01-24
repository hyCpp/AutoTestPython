# -*- coding: utf-8 -*-

import os
import platform
from airtest.core.android.adb import *
import cmd

class ADB(ADB):
    def __init__(self, serialno='192.168.5.111:5555', adb_path=None, server_addr=None):
        autost_path = __file__
        autost_path = autost_path[:autost_path.rfind(os.path.sep)]
        autost_path = autost_path[:autost_path.rfind(os.path.sep)]
        if not adb_path:
            if platform.system() == 'Windows':
                adb_path = os.path.sep.join([autost_path, "tools", "adb", "adb.exe"])
                os.system('%s devices > nul' % adb_path)
            else:
                adb_path = os.path.sep.join([autost_path, "tools", "adb", "adb"])
        super(ADB, self).__init__(serialno, adb_path, server_addr)
    
    def connect(self):
        self.cmd("connect %s" % self.serialno)
        self.cmd("root")
        self.cmd("connect %s" % self.serialno)
    
    @property
    def sdk_version(self):
        try:
            return super(ADB, self).sdk_version() or 14
        except:
            return 14
    
    @property
    def line_breaker(self):
        return b'\r\n'
    
    def snapshot(self):
        raw = self.cmd('shell screencap -p', ensure_unicode=True)
        return raw.replace(self.line_breaker, b"\n")
    
    def push(self, local, remote):
        print('push', local)
        self.cmd(["push", local, remote], ensure_unicode=True)

    def pull(self, remote, local):
        self.cmd(["pull", remote, local], ensure_unicode=True)
    
    def shell(self, cmd, ignore=""):
        print(cmd)
        try:
            super(ADB, self).shell(cmd)
        except Exception as e:
            if ignore and e.stderr.find(ignore) >= 0:
                pass
            else:
                raise
        