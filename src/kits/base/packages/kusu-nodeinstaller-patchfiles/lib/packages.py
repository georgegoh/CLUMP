#! /usr/bin/env python
#
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import kusu.genupdates.packagesack
import re
import fnmatch
from primitive.system.software.probe import OS
from sets import Set

def buildPkgRefDict(pkgs):
    """take a list of pkg objects and return a dict the contains all the possible
       naming conventions for them eg: for (name, 0, 1, i386)
       dict[name] = (name, 0, 1, i386)
       dict[name.i386] = (name, 0, 1, i386)
       dict[name-0-1.i386] = (name, 0, 1, i386)
       dict[name-0] = (name, 0, 1, i386)
       dict[name-0-1] = (name, 0, 1, i386)
    """
    pkgdict = {}
    for pkg in pkgs:
        if pkg.name is None:
            continue
        (n, v, r, a) = pkg.packageTuple()
        name = n
        nameArch = '%s.%s' % (n, a)
        nameVerRelArch = '%s-%s-%s.%s' % (n, v, r, a)
        nameVer = '%s-%s' % (n, v)
        nameVerRel = '%s-%s-%s' % (n, v, r)
        for item in [name, nameArch, nameVerRelArch, nameVer, nameVerRel]:
            if not pkgdict.has_key(item):
                pkgdict[item] = []
            pkgdict[item].append(pkg)
    
    return pkgdict

def parsePackages(pkgs, usercommands, casematch=0):
    """matches up the user request versus a pkg list:
       for installs/updates available pkgs should be the 'others list'
       for removes it should be the installed list of pkgs
       takes an optional casematch option to determine if case should be matched
       exactly. Defaults to not matching.
    """

    pkgdict = buildPkgRefDict(pkgs)
    exactmatch = []
    matched = []
    unmatched = []
    for command in usercommands:
        if pkgdict.has_key(command):
            exactmatch.extend(pkgdict[command])
            del pkgdict[command]
        else:
            # anything we couldn't find a match for
            # could mean it's not there, could mean it's a wildcard
            if re.match('.*[\*,\[,\],\{,\},\?].*', command):
                trylist = pkgdict.keys()
                restring = fnmatch.translate(command)
                if casematch:
                    regex = re.compile(restring) # case sensitive
                else:
                    regex = re.compile(restring, flags=re.I) # case insensitive
                foundit = False
                for item in trylist:
                    if regex.match(item):
                        matched.extend(pkgdict[item])
                        del pkgdict[item]
                        foundit = True

                if not foundit:
                    unmatched.append(command)

            else:
                if casematch:
                    unmatched.append(command)
                else:
                    # look for case insensitively
                    foundit = False
                    for item in pkgdict.keys():
                        if command.lower() == item.lower():
                            matched.extend(pkgdict[item])
                            foundit = True
                            continue

                    # we got nada
                    if not foundit:
                        unmatched.append(command)

    matched = unique(matched)
    matched_dict = {}
    for match in matched:
        try:
            matched_dict[match.name].append(match)
        except KeyError:
            matched_dict[match.name] = [match]
    
    unmatched = unique(unmatched)
    exactmatch = unique(exactmatch)
    return exactmatch, matched_dict, unmatched

def unique(s):
    """Return a list of the elements in s, but without duplicates.
    """
    
    return list(Set(s))

def comparePackageVersions(pkg1, pkg2):
    ver1_list = pkg1.ver.split('.')
    ver2_list = pkg2.ver.split('.')
    
    stop = len(ver1_list)
    pkg = pkg2
    if stop > len(ver2_list):
        stop = len(ver2_list)
        pkg = pkg1 #longer version is greater if all common version parts are equal (5.2.1 > 5.2)
    
    for i in range(stop):
        try:
            if int(ver1_list[i]) > int(ver2_list[i]):
                return pkg1
            elif int(ver1_list[i]) < int(ver2_list[i]):
                return pkg2
        except ValueError:
            return pkg1 #arbitrary - cannot compare (5.2.e ? 5.2.1)
    return pkg

def returnNewestPackage(pkglist):
    if 0 == len(pkglist):
        return None
    
    best = pkglist[0]
    for pkg in pkglist[1:]:
        best = comparePackageVersions(pkg, best)
    
    return best

def returnBestX86Package(pkglist, target_arch=None):
    myarch = OS()[2]
    if target_arch is not None:
        myarch = target_arch
    if myarch not in ['i386', 'i486', 'i586', 'i686']:
        return None
    myarch_int = int(myarch[1:])
    
    lowlist = []
    highlist = []
    higher_arch = 9999
    
    for pkg in pkglist:
        try:
            check_arch = int(pkg.arch[1:])
        except ValueError:
            continue
        
        if check_arch > myarch_int and check_arch <= higher_arch:
            highlist.append(pkg)
            higher_arch = check_arch
        elif check_arch <= myarch:
            lowlist.append(pkg)
    
    if 0 == len(pkglist) and len(highlist) > 0:
        return returnNewestPackage(highlist)
    return returnNewestPackage(pkglist)

def bestPackageFromList(pkglist, target_arch=None):
    myarch = OS()[2]
    if target_arch is not None:
        myarch = target_arch
    
    noarch = []
    arch64 = []
    arch86 = []
    
    for po in pkglist:
        if 'noarch' == po.arch:
            noarch.append(po)
        elif 'x86_64' == po.arch:
            arch64.append(po)
        elif po.arch in ['i386', 'i486', 'i586', 'i686']:
            arch86.append(po)
    
    noarch_best = returnNewestPackage(noarch)
    arch64_best = returnNewestPackage(arch64)
    arch86_best = returnBestX86Package(arch86, myarch)
    
    if noarch_best is None:
        if arch64_best is not None and 'x86_64' == myarch:
            return arch64_best
        else:
            return arch86_best
    else:
        return noarch_best

if '__main__' == __name__:
    import kusu.util.log as kusulog
    import os
    logger = kusulog.getKusuLog('kusu')
    logger.addFileHandler(os.environ['KUSU_LOGFILE'])
    sack = packagesack.PackageSack(logger)
    ll = sack.listPackages()
    e, m, u = parsePackages(ll, ['xen', 'crap', 'e*'])
    print 'exact\n'+'='*20
    for item in e:
        print item.fullName()
    print 'match\n'+'='*20
    for item in m:
        print item.fullName()
    print 'unmat\n'+'='*20
    for item in u:
        print str(item)
    print 'best\n'+'='*20
    best = bestPackageFromList(e)
    print str(best.fullName())
