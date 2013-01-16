#!/usr/bin/python

import os, sys

if __name__ == "__main__":
    version = sys.argv[1]
    release_id = sys.argv[2]
    rhel6_tarball =  [name for name in os.listdir("..") if name.endswith("el6.tar.bz2")][0]

    subject = "Subject: [ABS]Taobao-kernel Build Notify"
    body = """

This is sent from ABS automatically, to notify you that the build for YUM test branch has been started.
You can find the package in http://yum.corp.taobao.com/taobao/5/x86_64/test/kernel/ after its finish.
It's Build %s with %s, FYI.

Regards,
Taobao.com ABS
Core System R&D, Kernel Team
.""" % (release_id, rhel6_tarball)

    os.system("echo \"%s\" | /usr/sbin/sendmail `cat ../MAINTAINERS`" % (subject + body, ))

