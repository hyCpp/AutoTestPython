# -*- coding: utf-8 -*-

import os
import time
import autost.case.executor


class CManager:
    def __init__(self, cases, device, logdir, rounds, proc_list):
        print(cases, device, logdir, rounds)
        self.cases = cases
        self.device = device
        self.logdir = logdir
        self.rounds = int(rounds)
        self.proc_list = proc_list
    
    def setup_report(self, logdir):
        #
        report_file_name = time.strftime('summary_%Y%m%d_%H%M%S.txt',time.localtime(time.time()))
        if self.logdir and not os.path.exists(self.logdir):
            os.makedirs(self.logdir)
        reportfile = os.path.sep.join([self.logdir or self.cases, report_file_name])
        if os.path.exists(reportfile):
            os.remove(reportfile)
        self.reportfile = open(reportfile, 'w')
    
    def __del__(self):
        self.reportfile.flush()
        self.reportfile.close()
    
    def run(self):
        self.setup_report(self.logdir)
        caselist = self.get_case_list(self.cases)
        all_result = 0
        rounds = 0
        while self.rounds < 0 or rounds < self.rounds:
            try:
                if self.proc_list[0] == 0:
                    break
            except:
                pass
            rounds += 1
            for (case_name, case_target, device, logdir) in caselist:
                time_mark = time.strftime('%Y%m%d_%H%M%S',time.localtime(time.time()))
                logdir = os.path.sep.join([logdir or os.path.sep.join([case_target, 'log']), '%s.log.%s' % (case_name,time_mark)])
                result = autost.case.executor.execute(case=case_target,
                                                      device_uri=device,
                                                      logdir=logdir,
                                                      proc_list=self.proc_list)

                all_result |= result
                if result not in (0,1):
                    break
                self.reportfile.write('%s\t%s\t%s\n' % (case_target, time_mark, str(result)))
                self.reportfile.flush()
        return all_result
    
    def get_case_list(self, target):
        caselist = []
        if (
            os.path.isdir(target) and target.endswith('.air') 
            or 
            os.path.isfile(target) and target.endswith('.py')
            ):
            case_name = target[target.rfind(os.path.sep) : target.rfind('.')]
            caselist.append([case_name, target, self.device, self.logdir])
        else:
            if os.path.isdir(target):
                for sub in os.listdir(target):
                    sub_target = os.path.sep.join([target, sub])
                    caselist.extend(self.get_case_list(sub_target))
        return caselist

def handle(cases, device='iauto:///', logdir='', rounds=1, proc_list=[]):
    return CManager(cases, device, logdir, rounds, proc_list).run()
    