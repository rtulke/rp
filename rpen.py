#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
rpen: rpen is a color highlighter  based on egrep.

@author: Robert Tulke, rt@debian.sh
@copyright: GPLv2
@date: 2014-05-06
"""

import os
import sys
from optparse import OptionParser
from subprocess import Popen, PIPE, STDOUT

parser = OptionParser()
(options, args) = parser.parse_args()

colors = [
    ('red','01;31'),
    ('green','01;32'),
    ('yellow','01;33'),
    ('blue','01;34'),
    ('purple','0;35'),
    ('magenta','01;35'),
    ('cyan','01;36'),
    ('brown','0;33'),
    ]

if len(args) > 0:
    op = sys.stdin.read()
    for i,srch in enumerate(args):
        color = colors[i%len(colors)][1]
        env=os.environ.copy()
        env['GREP_COLORS'] = "mt="+color
        p = Popen(["egrep", srch+"|", "--color=always"], stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=env)
        op = p.communicate(input=op)[0]
    print(op)
else:
    print("sample usage of rpen:")
    rbegin,rend = '\033[35m','\033[0m'
    print("cat /var/log/syslog | " + rbegin + "rpen foo bar \" foobar\" " + rend + " | less -R")
