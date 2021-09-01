#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from optparse import OptionParser
from subprocess import Popen, PIPE, STDOUT

#if sys.version_info < (3, ):
#    print('Please upgrade your Python version to 3.7.0 or higher')
#    sys.exit()

parser = OptionParser("usage: cat logfile | %prog [options] searchterm1 searchterm2...")
parser.add_option("-i", action="store_true", dest="ignore_case", default=False, help="perform a case insensitive search")
parser.add_option("-k", action="store_true", dest="display_all", default=False, help="only highlight, do not filter")
(options, args) = parser.parse_args()

colors = [
    ('green','04;01;32'),
    ('yellow','04;01;33'),
    ('red','04;01;31'),
    ('blue','04;01;34'),
    ('purple','0;04;35'),
    ('magenta','04;01;35'),
    ('cyan','04;01;36'),
    ('brown','0;04;33'),
    ]

if len(args) == 0:
    parser.print_help()
    sys.exit()

op = sys.stdin.read()
if not options.display_all:
    if options.ignore_case:
        if sys.version_info > (3, ):
            p = Popen(["egrep", "|".join(args), "--color=always", "-i"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=os.environ.copy(),encoding="utf-8")
        else:
            p = Popen(["egrep", "|".join(args), "--color=always", "-i"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=os.environ.copy())

    else:
        if sys.version_info > (3, ):
            p = Popen(["egrep", "|".join(args), "--color=always"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=os.environ.copy(),encoding="utf-8")
        else:
            p = Popen(["egrep", "|".join(args), "--color=always"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=os.environ.copy())
    op = p.communicate(input=op)[0]
for i,srch in enumerate(args):
    color = colors[i%len(colors)][1]
    env=os.environ.copy()
    env['GREP_COLORS'] = "mt="+color

    if options.ignore_case:
        if sys.version_info > (3, ):
            p = Popen(["egrep", srch+"|", "--color=always", "-i"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=env,encoding="utf-8")
        else:
            p = Popen(["egrep", srch+"|", "--color=always", "-i"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=env)

    else:
        if sys.version_info > (3, ):
            p = Popen(["egrep", srch+"|", "--color=always"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=env,encoding="utf-8")
        else:
            p = Popen(["egrep", srch+"|", "--color=always"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=env)

    op = p.communicate(input=op)[0]
print(op)
