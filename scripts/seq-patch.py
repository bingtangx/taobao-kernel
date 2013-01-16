#!/usr/bin/python

#############################################################################
# Copyright (c) 2010, 2011 Taobao.com, Inc.
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
# This is a rework of opensuse's sequence-patch.sh in python.
#############################################################################

# Global imports (file level)
import os, sys, subprocess, tempfile
import config

# End of global imports

# Default configs
SCRATCH_AREA = "tmp"
QUIET = True
QUILT = True
VANILLA = False
# End of default configs



def print_usage ():
    pass

def rm_in_background (folder):
    subprocess.call(["rm", "-rf", folder])


def local_check_output(*popenargs, **kwargs):
    r"""Run command with arguments and return its output as a byte string.

    If the exit code was non-zero it raises a CalledProcessError.  The
    CalledProcessError object will have the return code in the returncode
    attribute and output in the output attribute.

    The arguments are the same as for the Popen constructor.  Example:

    >>> check_output(["ls", "-l", "/dev/null"])
    'crw-rw-rw- 1 root root 1, 3 Oct 18  2007 /dev/null\n'

    The stdout argument is not allowed as it is used internally.
    To capture standard error in the result, use stderr=STDOUT.

    >>> check_output(["/bin/sh", "-c",
    ...               "ls -l non_existent_file ; exit 0"],
    ...              stderr=STDOUT)
    'ls: non_existent_file: No such file or directory\n'
    """
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, output=output)
    return output

def  check_patch_version ():
    # We were told that some patches require patch 2.5.4
    version_out = subprocess.check_output(["patch", "--version"])
    major = int(version_out[6:7])
    middle = int(version_out[8:9])
    minor = int(version_out[10:11])
    if major < 2:
        return False
    if middle < 5:
        return False
    if middle ==5 and minor < 4:
        return False
    return True


def parse_opts ():
    import getopt
    global SCRATCH_AREA, QUIET, QUILT, VANILLA
    try:
        opts, args = getopt.getopt(sys.argv[1:], "qvd:",  \
                                   ["quilt", "no-quilt", "combine", \
                                    "arch=", "vanilla", \
                                    "dir="])
        for o, a in opts:
            if o in ("-q"):
                QUIET = True
            if o in ("-v"):
                QUIET = False
            if o in ("-d", "--dir"):
                SCRATCH_AREA = a.strip()
            if o in ("--quilt"):
                QUILT = True
            if o in ("--no-quilt"):
                QUILT = False
            if o in ("--vanilla"):
                VANILLA = True
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)


def get_script_loc ():
    path = sys.path[0]
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)


if __name__ == "__main__":
    parse_opts()

    # To compatbile with older python (<2.7)
    if not 'check_output' in dir(subprocess):
        subprocess.check_output = local_check_output

    IGNORE = open("/dev/null", "w")
    # To run on old RHELs, we don't check patch version here.
    # if not check_patch_version():
    #    print >>sys.stderr, "Patch version >= 2.5.4 is required.\n"
    #    sys.exit(1)


    stored_dir = os.getcwd()
    os.chdir(get_script_loc())
    # seq-patch.py is supposed to be located at $WORKING_DIR/scripts/
    os.chdir("..")

    # Guess where we are.
    WORKING_DIR = os.getcwd()
    SOURCE_DIR = os.path.join(WORKING_DIR, "redhat-kernel-source/linux-2.6.32")
    if not os.path.exists(SOURCE_DIR):
        print >>sys.stderr, "The dir of redhat kernel source is missing."
        sys.exit(1)
        
    if SCRATCH_AREA == "":
        print >>sys.stderr, "SCRATCH_AREA can not be null, roll back to \
            default value (tmp)\n"
        SCRATCH_AREA = "tmp"

    if not os.path.isdir(SCRATCH_AREA):
        if os.path.exists(SCRATCH_AREA):
            print >>sys.stderr, "The SCRATCH_AREA folder: %s already exists.\n"
            "Please specify an alternative name.\n" % (SCRATCH_AREA,)
            sys.exit(1)
        os.mkdir(SCRATCH_AREA)
    SCRATCH_AREA = os.path.join(os.getcwd(), SCRATCH_AREA)
    # ORIG_DIR is the folder where the unziped kernel source code lives, which
    # means vanilla kernel.
    ORIG_DIR = os.path.join(SCRATCH_AREA, "linux-%s.orig" % (config.get_srcversion(),))
    PATCH_DIR = os.path.join(SCRATCH_AREA, "linux-%s" % (config.get_srcversion(),))

    SCRIPTS_DIR = os.path.join(os.getcwd(), "scripts")
    if not os.path.exists(SCRIPTS_DIR):
        print >>sys.stderr, "Cannot find scripts folder.\n"
        sys.exit(1)


    if not os.path.exists("series.conf"):
        print >>sys.stderr, "Configuration file series.conf not found.\n"
        sys.exit(1)

    # Delete existed PATCH_DIR if it exists
    if os.path.exists(PATCH_DIR):
        rm_in_background(PATCH_DIR)

    # Create fresh $SCRATCH_AREA/linux-$SRCVERSION, that's to say ORIG_DIR.
    if not os.path.exists(ORIG_DIR): # If we are not re-using anything
        print >>sys.stdout, "Copying the Redhat kernel source tree as the code base."
        subprocess.call(["cp", "-r", SOURCE_DIR, ORIG_DIR])

        # Avoid writing into them by mistake...
        # os.system("find %s -type f| xargs chmod a-w+r" % (ORIG_DIR,))

    if not os.path.exists(ORIG_DIR):
        print >>sys.stderr, "Things won't continue without a working source tree.\n"
        sys.exit(1)

    # Create hardlinked patched tree
    ret = subprocess.call(["cp", "-rld", ORIG_DIR, PATCH_DIR])
    if ret:
        print >>sys.stderr, "Fail to generate PATCHDIR: %s" % (PATCH_DIR,)
        sys.exit(1)

    # Begin to patch PATCH_DIR with quilt
    os.chdir(PATCH_DIR)
    series_conf = open(os.path.join(WORKING_DIR, "series.conf"), "r")
    series = open(os.path.join(WORKING_DIR, "series"), "w")
    try:
#        guards_output= subprocess.Popen([os.path.join(SCRIPTS_DIR, "guard.py")], \
#                                     stdin = series_conf, stdout = subprocess.PIPE).communicate()[0].split("\n")
        guards_output= subprocess.Popen([os.path.join(SCRIPTS_DIR, "guard.py")], \
                                     stdin = series_conf, stdout = series)
        guards_output.wait()
    finally:
        series_conf.close()
        series.close()

#    for patch in guards_output:
#        patch = patch.strip()
#        if not patch:
#            continue
#        ret = subprocess.call(["quilt", "import", os.path.join(WORKING_DIR, patch.strip())])
#        if ret:
#            print >>sys.stderr, "Fail to apply %s" % (patch,)
#            sys.exit(1)

    # The idea here is to manage the patches by quilt after unpacking the tarball, the user
    # is able to add/delete/modify the patches under the $PATCH_DIR/patches. Add all the
    # patches in that folder will be gathered again by package.py, then the legacy ones under
    # $WORKING_DIR will be refreshed also.
    #

    dirs = []
    os.mkdir(os.path.join(PATCH_DIR, ".pc"))
    series = open(os.path.join(WORKING_DIR, "series"), "r").readlines()
    for p in series:
        pn = os.path.dirname(p)
        if not pn in dirs:
            os.makedirs(os.path.join(PATCH_DIR,  ".pc", pn))
            dirs.append(pn)

    os.symlink(WORKING_DIR, os.path.join(PATCH_DIR, "patches"))
    os.symlink(os.path.join(WORKING_DIR, "scripts", "refresh_patch.sh"), \
               os.path.join(PATCH_DIR, "refresh_patch.sh"))
    os.symlink(os.path.join(WORKING_DIR, "scripts", "run_oldconfig.py"), \
               os.path.join(PATCH_DIR, "run_oldconfig.py"))

    try:
        subprocess.check_output(["quilt", "upgrade"])
    except:
        print >>sys.stderr, "\nDo you have quilt?\n"
        sys.exit(1)

    quilt_run = subprocess.Popen(["quilt", "push", "-a"])
    ret = quilt_run.wait()
    if ret:
        print >>sys.stderr, "\nFail to apply the above patch.\n"
        sys.exit(1)

    os.chdir(stored_dir)
    IGNORE.close()



