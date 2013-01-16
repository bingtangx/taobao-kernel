# Configs for various python scripts

import os, sys, subprocess
# The version of the main tarball to use
# This is the version number of Redhat Enterprise Linux as our build's base.
# Our base version can be tripped out from it.
SRCVERSION = None
# Variant of the kernel-source package, it's useless for now.
# This is supposed to be used to different the various kernels for different platforms and
# applications in the future
BUILD_DIR = "taobao-kernel-build"
VARIANT="tbpublic"
# Supported archs, x86_64 only for now.
flavor_archs = ['x86_64']


MACROS = {
    # These are relevant to release process, I hard code them here
    # until we set down the process.
        "RELEASED_KERNEL":0,
#          "BUILD": "71.7.1",
#         "SUBLEVEL": 32,
          "RCREV": 0, # 1 if it's a RC
          "GITREV": 0, # These two ones are useless now.
}
# Whether we are under a git repo
def whether_using_git():
    using = True
    IGNORE = open("/dev/null", "w")
    ret = 1
    try:
        git = subprocess.Popen(["git", "rev-parse", "HEAD"], stdout = IGNORE, stderr = IGNORE)
        ret = git.wait()
    except:
        using = False
    if ret:
        using = False
    IGNORE.close()
    return using

def get_branch_name():
    scripts_dir = os.getcwd()
    branch_name = ""
    try:
        head_name = os.path.join(scripts_dir,  "..",  ".git", "HEAD")
        sed = subprocess.Popen(["sed", "-ne", "s|^ref: refs/heads/||p", head_name], stdout=subprocess.PIPE).communicate()[0].split("\n")
        branch_name = sed[0]
    except:
        branch_name = "unknown-branch"
    return branch_name

def get_srcversion():
    global SRCVERSION
    if SRCVERSION:
        return SRCVERSION
    SRCVERSION = open(os.path.dirname(os.path.abspath(sys.argv[0])) + "/../redhat-kernel-version").readline()[6:-1]
    return SRCVERSION

