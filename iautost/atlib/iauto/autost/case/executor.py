# -*- coding: utf-8 -*-

import os
import sys
import time
import shutil
import json
from autost.api import *

class CProcess:
    def __init__(self, case, device_uri, logdir, issync, proc_list):
        self.case = case
        self.device_uri = device_uri
        self.logdir = logdir
        self.issync = issync
        self.proc_list = proc_list
        (self.casename, self.casedir, self.casefile) = self.get_case_info(case)
        self.setup_log(logdir)
    
    def get_case_info(self, case):
        #
        casedir = os.path.abspath(case)
        if casedir.endswith('.py'):
            casedir = casedir[:casedir.rfind(os.path.sep)]
        
        #
        casename = casedir[casedir.rfind(os.path.sep)+1: -4]
        
        #
        casefile = os.path.abspath('%s/%s.py' % (casedir, casename))
        
        #
        return (casename, casedir, casefile)
    
    def setup_log(self, logdir):
        #
        if not logdir:
            logdir = os.path.sep.join([self.casedir, 'log'])
        self.logdir = logdir
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        
        #
        time_mark = time.strftime('%Y%m%d_%H%M%S',time.localtime(time.time()))
        log_file_name = 'log_%s_%s.txt' % (self.casename, time_mark)
        logfile = os.path.sep.join([logdir, log_file_name])
        if os.path.exists(logfile):
            os.remove(logfile)
        self.logfile = open(logfile, 'w')
    
    def __del__(self):
        self.logfile.flush()
        self.logfile.close()

    def run(self):
        #
        print('================================================================')
        print('casedir:', self.casedir)
        print('casename:', self.casename)
        print('casefile:', self.casefile)
        if self.issync:
            result = self._execute(self.casedir, self.casefile)
        else:
            try:
                process(self.case, self.device_uri, self.logdir)
                result = 0
            except:
                result = 1
                import traceback
                traceback.print_exc()
        result_str = 'Passed' if result == 0 else 'Failed'
        sys.stdout.write('case result: %s(%i)\n' % (result_str, result))
        self.logfile.write('case result: %s(%i)\n' % (result_str, result))
        print('================================================================')

        return result
    
    def _execute(self, pythondir, pythonfile):
        import PyQt5.QtCore
        self.proc = PyQt5.QtCore.QProcess()
        self.proc_list.append(self.proc)
        self.proc.setWorkingDirectory(pythondir)
        self.proc.readyReadStandardError.connect(self.error)
        self.proc.readyReadStandardOutput.connect(self.output)
        self.proc.start('python', ['-u', __file__, pythonfile, '--device', self.device_uri, '--logdir', self.logdir])
        #self.proc.terminate()
        self.proc.waitForFinished(300 * 1000)
        return self.proc.exitCode()
    
    def output(self):
        log = self.proc.readAllStandardOutput()
        sys.stdout.write(str(log, encoding='utf8'))
        self.logfile.write(str(log, encoding='utf8'))
    
    def error(self):
        log = self.proc.readAllStandardError()
        sys.stderr.write(str(log, encoding='utf8'))
        self.logfile.write(str(log, encoding='utf8'))

def execute(case, device_uri='iauto:///', logdir='', issync=True, proc_list=None):
    return CProcess(case, device_uri, logdir, issync, proc_list).run()

def process(target, device_uri, logdir):
    #
    folder = target[:target.rfind(os.path.sep)]
    case_name = target[target.rfind(os.path.sep) + 1: -3]
    sys.path.append(folder)
    G.BASEDIR.append(folder)
    #os.chdir(folder)
        
    #
    device_uri_list = device_uri.split('||')
    for uri in device_uri_list:
        print('Connecting device : %s' % uri)
        connect_device(uri)
    #
    print("case setup...")
    if os.path.exists(r'config.ini'):
        configs = json.load(open(r'config.ini'))
        setup_cases = configs.get('setups', [])
        for setup_case in setup_cases:
            print("case setup %s..." % setup_case)
            setup_file_name = setup_case[setup_case.rfind('/') + 1: -3]
            os.chdir(folder)
            setup_dir = os.path.abspath(os.sep.join(setup_case.split('/')[:-1]))
            sys.path.insert(0, setup_dir)
            os.chdir(setup_dir)
            __import__(setup_file_name)
            del sys.modules[setup_file_name]
            sys.path.pop(0)
    
    #
    print("case run...")
    os.chdir(folder)
    if case_name in sys.modules:
        del sys.modules[case_name]
    #ST.REPORT_DIR = logdir
    ST.LOG_DIR = logdir
    time_mark = time.strftime('%Y%m%d_%H%M%S',time.localtime(time.time()))
    G.LOGGER.set_logfile(os.path.sep.join([logdir, 'report_%s_%s.txt' % (case_name, time_mark)]))
    
    #
    if not os.path.exists(target):
        raise RuntimeError("case file not exists, %s..." % target)
    else:
        try:
            start_listen()
            __import__(case_name)
        except:
            #
            print('case fail...')
            ST.LOG_DIR = None
            G.LOGGER.set_logfile(None)
            
            #
            if os.path.exists(r'config.ini'):
                configs = json.load(open(r'config.ini'))
                teardown_cases = configs.get('teardowns', [])
                for teardown_case in teardown_cases:
                    print("case teardown %s..." % teardown_case)
                    teardown_file_name = teardown_case[teardown_case.rfind('/') + 1: -3]
                    os.chdir(folder)
                    teardown_dir = os.path.abspath(os.sep.join(teardown_case.split('/')[:-1]))
                    sys.path.insert(0, teardown_dir)
                    os.chdir(teardown_dir)
                    __import__(teardown_file_name)
                    del sys.modules[teardown_file_name]
                    sys.path.pop(0)
            #
            #if teardown_file_name == 'hulog':
            if hasattr(device(), 'fetch_log'):
                print('fetch hu log...')
                device().fetch_log(pc_log_path=logdir)
            
            #
            raise
        finally:
            stop_listen()
    
    G.LOGGER.set_logfile(None)
    print("case end.")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='run route bin data')
    #parser.add_argument('executor', help='executor py file')
    parser.add_argument('target', help='case py file')
    parser.add_argument('--device', dest='device', default='iauto:///')
    parser.add_argument('--logdir', dest='logdir', default='')
    args = parser.parse_args()
    
    from autost.api import *
    process(args.target, args.device, args.logdir)
    
    
    
