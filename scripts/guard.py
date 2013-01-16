#!/usr/bin/python

#############################################################################
# Copyright (c) 2003-2005,2007-2009 Taobao.com, Inc.
# All Rights Reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact Taobao.com, Inc.
#
# To contact Taobao.com about this file by physical or electronic mail,
# you may find current contact information at www.taobao.com
#
# This is a rework of opensuse's scripts/guards in python.
#############################################################################

# It reads lines of the names of the patches from stdin
# Guards:
# -xxx   exclude if xxx is defined
#+xxx   include if xxx is defined

# There are two ways to define a symbol
# 1) By adding a "#define xxx" line in the conf file
# 2) By running guard.py with "guard.py xxx yyy" arguments

import os, sys
import re, getopt

if __name__ == "__main__":
    prefix =""

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["prefix=", "list"])
        for o, a in opts:
            if o in ("--prefix"):
                prefix = a.strip()
    except:
        sys.exit(1)

    symbols = []
    symbols.extend(sys.argv[1:])
    s = r".*define\s+(\S+)"
    # For all the lines which have "+name xx.patch"
    # xx.patch will be print out if name is defined.
    d = r"\s*\+(\S+)\s+(\S+)"
    # For all the lines which have "-name yy.patch"
    # yy.patch will not be print out if name is defined.
    e = r"\s*\-(\S+)\s+(\S+)"
    p = re.compile(s)
    q = re.compile(d)
    o = re.compile(e)

    old = sys.stdin.readlines()
    for line in old:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            m  = p.match(line)
            if m:
                symbols.append(m.group(1))
        elif line.startswith("+"):
            m = q.match(line)
            if m:
                name =m.group(1)
                if name in symbols:
                    print >>sys.stdout, os.path.join(prefix, m.group(2).strip())
        elif line.startswith("-"):
            m = o.match(line)
            if m:
                name = m.group(1)
                if name in symbols:
                    continue
                else:
                    print >>sys.stdout, os.path.join(prefix, m.group(2).strip())
        else:
            print >>sys.stdout, os.path.join(prefix, line.strip())
