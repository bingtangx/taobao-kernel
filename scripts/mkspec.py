#!/usr/bin/python

#############################################################################
# Copyright (c) 2010 Taobao.com, Inc.
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

import os, subprocess, sys
import commands, getopt, shutil

import config

patch_start_no = 200
config_start_no = 50

def print_usage ():
    print >>sys.stderr, "Usage: mkspec.py --patches <patches' names, splited with spaces>\n" \
        "--release-string <release string>\n" \
        "--configs <config files' names>\n" \
        "--changelog <Changelog file's name>\n" \
        "[--release <mark for a kernel release>]\n"
    return


def parse_opts ():
    import getopt
    release_string = None
    configs = []
    changelog = None
    released = False
    buildid = ""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "",  \
                                   ["buildid=", "patches=", "release-string=", "configs=", "changelog=", "release", "help"])
        for o, a in opts:
            if o in ("--help"):
                print_usage()
                sys.exit(2)
            if o in ("--patches"):
                patches = a.strip().split(" ")
            if o in ("--buildid"):
                buildid = a.strip()
            if o in ("--release-string"):
                if " " in a.strip():
                    print >>sys.stderr, "--release-string option argument must not contain spaces\n"
                    sys.exit(1)
                release_string = a.strip()
            if o in ("--configs"):
                configs = a.strip().split(" ")
            if o in ("--changelog"):
                changelog = a.strip()
            if o in ("--release"):
                released  = True
    except:
        print_usage()
        sys.exit(2)
    return patches, release_string, configs, changelog, released, buildid

def get_script_loc ():
    path = sys.path[0]
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)



if __name__ == "__main__":
    patches, release_string, config_files, changelog, released, buildid = parse_opts()
    script_dir = get_script_loc()
    os.chdir(script_dir)
    os.chdir("..")
    WORKING_DIR = os.getcwd()
    rpm_dir = os.path.join(WORKING_DIR,  "rpm")
    build_dir = os.path.join(WORKING_DIR, config.BUILD_DIR)
    config_dir = os.path.join(WORKING_DIR,  "config")

    spec_temple = "".join(open(os.path.join(rpm_dir,  "kernel.spec.in")).readlines())

    # Generate version number from tags and base kernel version number.
    # tb_base_var is something like 2.6.32
    tb_base_ver = config.get_srcversion().split("-")[0]
    rh_release_id = config.get_srcversion().split("-")[1][:-4]
    tb_sublevel = tb_base_ver.split(".")[2]

    try:
        tb_short_commit = commands.getoutput("git log --pretty=format:%%h -1")
        tb_long_commit = commands.getoutput("git log --pretty=format:%H -1")
    except:
        tr_short_commit = tb_long_commit = "UnknownCommitId"

    # the lst string is distribution id, for,
    # branch master, it's ".master"
    # branch 5u4, it's ".el5"
    # branch 6u, it's ".el6"
    pkg_release = rh_release_id + "."  + "tb" + buildid + ".el6"

    dynamic_values = {"RPMVERSION" : tb_base_ver,
                      "PKG_RELEASE" : pkg_release,
                      "KVERSION" : config.get_srcversion(),
                      "SUBLEVEL" : tb_sublevel,
                      "COMMITID" : tb_long_commit,
                      "RHELBASE" : "kernel-" + config.get_srcversion()
                      }

    for key in dynamic_values.keys():
        spec_temple = spec_temple.replace("%%" + key + "%%", str(dynamic_values[key]))


    for key in config.MACROS.keys():
        spec_temple = spec_temple.replace("%%" + key + "%%", str(config.MACROS[key]))

    configs = ""
    index = config_start_no
    for cn in config_files:
        configs += "Source%d: %s\n" % (index, cn)
        index +=1
    spec_temple = spec_temple.replace("%%CONFIGS%%", configs)

    text = ""
    applypatch = ""
    index = patch_start_no
    for cn in patches:
        text += "Source%d: %s\n" % (index, cn)
        applypatch +="tar xjf %%{SOURCE%d}\n" % (index,)
        index +=1

    applypatch += "%_sourcedir/apply-patches.sh %_sourcedir/series.conf .\n"
    for cn in patches:
        applypatch += "rm -rf `echo %s|sed 's/.tar.bz2//'`\n" % (cn,)


    spec_temple = spec_temple.replace("%%PATCH_LIST%%", text)
    spec_temple = spec_temple.replace("%%PATCH_APPLICATION%%", applypatch)

    changes = ""
    if changelog:
        changes = "".join(open(changelog).readlines())

    spec_temple = spec_temple.replace("%%CHANGELOG%%", changes)

    spec = open(os.path.join(build_dir,  "kernel.spec"), "w")
    spec.write(spec_temple)
    spec.close()
