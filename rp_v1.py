#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
import argparse
from subprocess import Popen, PIPE, STDOUT

def main():
    parser = argparse.ArgumentParser(description="Searches and highlights search terms in the input.")
    parser.add_argument("searchterms", nargs='+', help="Search terms")
    parser.add_argument("-i", "--ignore-case", action="store_true", help="Ignore case distinctions")
    parser.add_argument("-k", "--display-all", action="store_true", help="Display all lines, only highlight")
    args = parser.parse_args()

    colors = [
        ('green', '04;01;32'),
        ('yellow', '04;01;33'),
        ('red', '04;01;31'),
        ('blue', '04;01;34'),
        ('purple', '0;04;35'),
        ('magenta', '04;01;35'),
        ('cyan', '04;01;36'),
        ('brown', '0;04;33'),
    ]

    if not args.searchterms:
        parser.print_help()
        sys.exit()

    # Reads from standard input
    op = sys.stdin.read()

    # Filters the input if -k is not set
    if not args.display_all:
        pattern = "|".join(args.searchterms)
        egrep_cmd = ["egrep", "--color=always"]
        if args.ignore_case:
            egrep_cmd.append("-i")
        egrep_cmd.append(pattern)

        p = Popen(egrep_cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, env=os.environ.copy(), universal_newlines=True)
        op, _ = p.communicate(input=op)

    # Highlights the search terms
    for i, srch in enumerate(args.searchterms):
        color = colors[i % len(colors)][1]
        env = os.environ.copy()
        env['GREP_COLORS'] = "mt=" + color

        egrep_cmd = ["egrep", "--color=always"]
        if args.ignore_case:
            egrep_cmd.append("-i")
        egrep_cmd.append(srch + "|")

        p = Popen(egrep_cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, env=env, universal_newlines=True)
        op, _ = p.communicate(input=op)

    print(op, end='')

if __name__ == "__main__":
    main()
