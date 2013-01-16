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
#############################################################################

# generate a kernel-source rpm package

# Global imports
import os, sys, subprocess, shutil
import config, tempfile
import commands, sets
from config import BUILD_DIR as BUILD_DIR
BUILDID=""
# End of global imports

# Default configs
tolerate_unknown_configs = False
mkspec_args = []

RELEASE_STRING = None
TSFILE = "source-timestamp"
misc_files_to_copy = ["series.conf", "scripts/merge.pl", \
                      "rpm/fullbuild.sh", "rpm/Makefile.common","scripts/perf","scripts/kabitool","scripts/check-kabi", \
                      "scripts/genkey", "scripts/perf-archive", "scripts/find-provides", "scripts/extrakeys.pub", \
                      "rpm/Makefile.config", "scripts/getarch.py", "scripts/apply-patches.sh", "scripts/guard.py"]
# End of default configs

using_git = config.whether_using_git()
tar_override_works = None

def print_usage ():
    print >>sys.stderr, "Usage: package.py [-h, --help <show usage>]\n" \
        "[-d, --dir <specify the target dir for output>]\n" \
        "[--release-string <specify the release string>]\n" \
        "[--release <specify if this is a relased kernel package>]\n" \
        "[--buildid <the build serial number on ABS>]\n"

def parse_opts ():
    global BUILD_DIR, BUILDID
    released = False
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:",  \
                                   ["dir=", "release-string=", "help",  "release", \
                                    "buildid="])
        for o, a in opts:
            if o in ("-d", "--dir"):
                BUILD_DIR = a.strip()
            if o in ("-h", "--help"):
                print_usage()
                sys.exit(2)
            if o in ("--release"):
                released = True
            if o in ("--buildid"):
                BUILDID = a.strip()
            if o in ("--release-string"):
                if " " in a.strip():
                    print >>sys.stderr, "--release-string option argument must not contain spaces\n"
                    sys.exit(1)
                RELEASE_STRING = a.strip()
    except:
        print_usage()
        sys.exit(2)

    if BUILDID == "":
        print >>sys.stdout, "Using buildid=1 as it's not specified.\n"
        BUILDID = "1"

    return released


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

def get_script_loc ():
    path = sys.path[0]
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)

def stable_tar(archive, files, mtime = None, chdir = ".", tar_opts = ""):
    global tar_override_works
    if chdir != ".":
        old_dir = os.getcwd()
    if tar_override_works is None: # Whether this works is unknown
        if not os.system("tar --mtime=\"Tue, 3 Feb 2009 10:52:55 +0100\" --owner=nobody \
                    --group=nobody --help 1>/dev/null 2>&1"):
            tar_override_works = True
        else:
            tar_override_works = False

    if tar_override_works:
        if mtime is None and using_git:
            mtime = "--mtime %s" % (subprocess.check_output(["git", "log", "-1",\
                                                             "--pretty=format:%cD"] + files))
        tar_opts += "--owner=nobody --group=nobody %s" %(mtime,)
    if chdir != ".":
        os.chdir(chdir)
    os.system("find %s \( -type f -o -type l -o -type d -a -empty \) "
              "-print0|LC_ALL=C sort -z| tar -cf - --null -T -|bzip2 -9 > %s" % (" ".join(files), archive))
    if chdir != ".":
        os.chdir(old_dir)



if __name__ == "__main__":
    released = parse_opts()

    # To compatbile with older python (<2.7)
    if not 'check_output' in dir(subprocess):
        subprocess.check_output = local_check_output

    IGNORE = open("/dev/null", "w")
    stored_dir = os.getcwd()
    script_dir = get_script_loc()
    os.chdir(script_dir)
    # seq-patch.py is supposed to be located at $WORKING_DIR/scripts/
    os.chdir("..")

    WORKING_DIR = os.getcwd()
    rpm_dir = os.path.join(WORKING_DIR,  "rpm")
    if  config.BUILD_DIR == "":
        print >>sys.stderr, "BUILD_DIR can not be null, roll back to \
            default value (taobao-kernel-build)\n"
        BUILD_DIR = "taobao-kernel-build"

    BUILD_DIR = os.path.join(WORKING_DIR, BUILD_DIR)
    SOURCE_DIR = os.path.join(WORKING_DIR, "redhat-kernel-source/linux-2.6.32")
    rh_changelog = os.path.join(WORKING_DIR, "redhat-kernel-changelog")
    if not os.path.exists(rh_changelog):
        print >>sys.stderr, "redhat-kernel-source\redhat-kernel-changelog is missing.\n"
        sys.exit(1)


    try:
        shutil.rmtree(BUILD_DIR)
    except:
        pass

    os.mkdir(BUILD_DIR)


    tarball_name = "linux-" + config.get_srcversion() + ".tar.bz2"
    tmp_name = "linux-" + config.get_srcversion()
    print >>sys.stdout, "%s\n" % (tarball_name,)
    os.rename(SOURCE_DIR, tmp_name) 

    subprocess.call(["tar", "cjf", tarball_name, tmp_name])
    os.rename(tarball_name, os.path.join(BUILD_DIR, tarball_name))
    os.rename(tmp_name, SOURCE_DIR)


    if not os.path.exists("series.conf"):
        print >>sys.stderr, "Configuration file series.conf not found.\n"
        sys.exit(1)


    for x in misc_files_to_copy:
        shutil.copy(x, BUILD_DIR)

#    os.chmod(os.path.join(BUILD_DIR, "series.conf"), 644)


    referenced_files = commands.getoutput("%s < series.conf |sort -u" \
                                          % (os.path.join(script_dir, "guard.py"), ))

    # referenced_files += "\n"

    config_files = commands.getoutput("%s < config.conf |sort -u" \
                                          % (os.path.join(script_dir, "guard.py"), ))
    os.environ["referenced_files"] = referenced_files
    refiles = referenced_files.split("\n")
    configs = config_files.split("\n")

    for x in configs:
        shutil.copy(os.path.join("config",  x), BUILD_DIR)

    tsfile = os.path.join(BUILD_DIR, TSFILE)

    if using_git:
        # Always include the git revision
        os.environ["stamp"] = tsfile
        # Generate time stamp file in $BUILD_DIR
        os.system(os.path.join(script_dir,  "add-timestamp.sh"))

    # Todo: trap EXIT signals to clean the temp files.

    # CLEANFILES=()
    # trap 'if test -n "$CLEANFILES"; then rm -rf "${CLEANFILES[@]}"; fi' EXIT
    # tmpdir=$(mktemp -dt ${0##*/}.XXXXXX)
    # CLEANFILES=("${CLEANFILES[@]}" "$tmpdir")

    os.system("cp -r rpm/ config.conf doc/ %s" % (BUILD_DIR,))
    changelog = os.path.join(BUILD_DIR, "taobao-kernel.changes")
    try:
        os.remove(os.path.join(BUILD_DIR, changelog, ".old"))
    except:
        pass

    # os.system("scripts/gitlog2changes HEAD > %s" % (changelog,))
    shutil.copyfile(os.path.join(WORKING_DIR, "kernel-source.changes"), changelog)

    all_archives = sets.Set([x.split("/")[0] for x in refiles])
    for archive in all_archives:
        files = None
        files = [x for x in refiles if archive in os.path.dirname(x)]
        if files:
            print >>sys.stdout, "%s.tar.bz2" % (archive,)
            stable_tar(os.path.join(BUILD_DIR,  archive + ".tar.bz2"),  files)

# Create empty dummys for any *.tar.bz2 archive mentioned in the spec file
# not already created. Therefore we don't have to modify the spec template
# if some patches folder is empty.
    archives = commands.getoutput(r"sed -ne 's,^Source[0-9]*:.*[ \t/]\([^/]*\)\.tar\.bz2$,\1,p' \
           %s | sort -u" % (os.path.join(rpm_dir, "kernel.spec.in"))).split("\n")
    for archive in archives:
        if "%" in archive:
            # Skip unresolved macro.
            continue
        if os.path.exists(os.path.join(BUILD_DIR, archive)):
            continue
        print >>sys.stdout, "%s.tar.bz2 (empty)" % (archive,)
        tmpdir = tempfile.mkdtemp()
        tmparchive = os.mkdir(os.path.join(tmpdir, archive))
        stable_tar(os.path.join(BUILD_DIR, archive + ".tar.bz2"), archive, \
                   mtime = "Wed, 01 Apr 2009 12:00:00 +0200", chdir = tmpdir)
        shutil.rmtree(tmpdir)
    cmd = os.path.join(script_dir, "mkspec.py") + " --patches \"%s\"" % (" ".join([n + ".tar.bz2" for n in all_archives]))  \
                      + " --configs \"%s\"" % (" ".join(configs), ) + " --changelog %s" % (rh_changelog, ) + " --buildid %s" % \
                      (BUILDID,)
    if RELEASE_STRING:
        cmd = cmd + " --release-string %s" % (RELEASE_STRING, )
    if released:
        cmd = cmd + " --release"
    os.system(cmd)
    os.chdir(stored_dir)
    IGNORE.close()
