#!/usr/bin/python
#

import os

# dict mapping arch -> ( multicompat, best personality, biarch personality )
multilibArches = { "x86_64":  ( "athlon", "x86_64", "athlon" ),
                   "sparc64": ( "sparc", "sparc", "sparc64" ),
                   "ppc64":   ( "ppc", "ppc", "ppc64" ),
                   "s390x":   ( "s390", "s390x", "s390" ),
                   "ia64":    ( "i686", "ia64", "i686" )
                   }

arches = {
    # ia32
    "athlon": "i686",
    "i686": "i586",
    "i586": "i486",
    "i486": "i386",
    "i386": "noarch",
    
    # amd64
    "x86_64": "athlon",
    "amd64": "x86_64",
    "ia32e": "x86_64",
    
    # itanium
    "ia64": "i686",
    
    # ppc
    "ppc64pseries": "ppc64",
    "ppc64iseries": "ppc64",    
    "ppc64": "ppc",
    "ppc": "noarch",
    
    # s390{,x}
    "s390x": "s390",
    "s390": "noarch",
    
    # sparc
    "sparc64": "sparcv9",
    "sparcv9": "sparcv8",
    "sparcv8": "sparc",
    "sparc": "noarch"
    }

# this computes the difference between myarch and targetarch
def archDifference(myarch, targetarch):
    if myarch == targetarch:
        return 1
    if arches.has_key(myarch):
        ret = archDifference(arches[myarch], targetarch)
        if ret != 0:
            return ret + 1
        return 0
    return 0

def score(arch):
    return archDifference(canonArch, arch)

def getCanonX86Arch(arch):
    # only athlon vs i686 isn't handled with uname currently
    if arch != "i686":
        return arch

    # if we're i686 and AuthenticAMD, then we should be an athlon
    f = open("/proc/cpuinfo", "r")
    lines = f.readlines()
    f.close()
    for line in lines:
        if line.startswith("vendor") and line.find("AuthenticAMD") != -1:
            return "athlon"
        # i686 doesn't guarantee cmov, but we depend on it
        elif line.startswith("flags") and line.find("cmov") == -1:
            return "i586"

    return arch

def getCanonPPCArch(arch):
    # FIXME: should I do better handling for mac, etc?
    if arch != "ppc64":
        return arch

    machine = None
    f = open("/proc/cpuinfo", "r")
    lines = f.readlines()
    f.close()
    for line in lines:
        if line.find("machine") != -1:
            machine = line.split(':')[1]
            break
    if machine is None:
        return arch

    if machine.find("CHRP IBM") != -1:
        return "ppc64pseries"
    if machine.find("iSeries") != -1:
        return "ppc64iseries"
    return arch

def getCanonX86_64Arch(arch):
    if arch != "x86_64":
        return arch

    vendor = None
    f = open("/proc/cpuinfo", "r")
    lines = f.readlines()
    f.close()
    for line in lines:
        if line.startswith("vendor_id"):
            vendor = line.split(':')[1]
            break
    if vendor is None:
        return arch

    if vendor.find("Authentic AMD") != -1:
        return "amd64"
    if vendor.find("GenuineIntel") != -1:
        return "ia32e"
    return arch
        
def getCanonArch(skipRpmPlatform = 0):
    if not skipRpmPlatform and os.access("/etc/rpm/platform", os.R_OK):
        try:
            f = open("/etc/rpm/platform", "r")
            line = f.readline()
            f.close()
            (arch, vendor, opersys) = line.split("-", 2)
            return arch
        except:
            pass
        
    arch = os.uname()[4]

    if (len(arch) == 4 and arch[0] == "i" and arch[2:4] == "86"):
        return getCanonX86Arch(arch)

    if arch.startswith("ppc"):
        return getCanonPPCArch(arch)
    if arch == "x86_64":
        return getCanonX86_64Arch(arch)

    return arch

# this gets you the "compat" arch of a biarch pair
def getMultiArchInfo(arch = getCanonArch()):
    if multilibArches.has_key(arch):
        return multilibArches[arch]
    if arches.has_key(arch) and arches[arch] != "noarch":
        return getMultiArchInfo(arch = arches[arch])
    return None

# get the best usual userspace arch for the arch we're on.  this is
# out arch unless we're on an arch that uses the secondary as its
# userspace (eg ppc64, sparc64)
def getBaseArch():
    arch = canonArch

    if arch == "sparc64":
        arch = "sparc"

    if arch.startswith("ppc64"):
        arch = "ppc"

    return arch

canonArch = getCanonArch()
