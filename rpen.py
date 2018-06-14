#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
rpen: rpen is a text highlighter  based on egrep.

@author: Robert Tulke, rt@debian.sh
@copyright: GPLv2
@date: 2014-05-06

18aug16: alp, added: if first arg i --> case_insensitive
"""

import os
import sys
from optparse import OptionParser
from subprocess import Popen, PIPE, STDOUT

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
        p = Popen(["egrep", "|".join(args), "--color=always", "-i"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=os.environ.copy())
    else:
        p = Popen(["egrep", "|".join(args), "--color=always"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=os.environ.copy())
    op = p.communicate(input=op)[0]
for i,srch in enumerate(args):
    color = colors[i%len(colors)][1]
    env=os.environ.copy()
    env['GREP_COLORS'] = "mt="+color

    if options.ignore_case:
        p = Popen(["egrep", srch+"|", "--color=always", "-i"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=env)
    else:
        p = Popen(["egrep", srch+"|", "--color=always"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=env)

    op = p.communicate(input=op)[0]
print(op)
