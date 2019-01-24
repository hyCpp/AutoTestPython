# -*- coding: utf-8 -*-

import os
import sys
import autost.case.executor
import autost.case.manager

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='run route bin data')
    parser.add_argument('case', help='case directory or case py file')
    parser.add_argument('--device', dest='device', default='iauto:///?ip=127.0.0.1&port=5391')
    parser.add_argument('--logdir', dest='logdir', default=None, help='log directory')
    parser.add_argument('--rounds', dest='rounds', default=1, help='case execute round')
    args = parser.parse_args()
    
    #
    #result = autost.case.executor.execute(args.case, args.device, args.logdir)
    result = autost.case.manager.handle(args.case, args.device, args.logdir, args.rounds)
    sys.exit(result)
    