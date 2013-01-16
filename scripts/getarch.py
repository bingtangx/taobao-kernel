#!/usr/bin/python
import sys

if __name__ == "__main__":
    arch = ""
    for line in sys.stdin:
        if line.startswith("#"):
            continue
        if "CONFIG_X86_64=y" in line:
            arch = "x86_64"
            break
        # More arch comes here.
    if arch:
        print >>sys.stdout, arch 
    else:
        print >>sys.stdout, "unknown-arch" 
