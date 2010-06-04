#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

#from kusu.buildkit.strategies.kitsource01 import KitSrcFactory, KusuKit, KusuComponent
import kusu.buildkit.strategies.kitsource01 as kitsource01
from kusu.buildkit.methods import *
from kusu.util.tools import getArch
from path import path

def getKitScript(kitsrc, kitscript='build.kit'):
    """ Sweeps the kitsrc dir and attempts to locate the kitscript.
    """
    _kitsrc = path(kitsrc)
    li = _kitsrc.files(kitscript)
    if not li: raise FileDoesNotExistError, kitscript
        
    # TODO : only handle single kitscript
    return li[0]

        
def loadKitScript(kitscript):
    """ Loads the kitscript and get a tuple of the kit, components and packages defined in
        that kitscript.
    """
    ns = {}
    execfile(kitscript,globals(),ns)
        
    pkgs = [ns[key] for key in ns.keys() if isinstance(ns[key], PackageProfile)]
    comps = [ns[key] for key in ns.keys() if isinstance(ns[key], kitsource01.KusuComponent)]
    kits = [ns[key] for key in ns.keys() if isinstance(ns[key], kitsource01.KusuKit)]
        
    # FIXME: only a single kit is supported right now
    if not kits:
        kit = []
    else:
        kit = kits[0]
        
    return (kit,comps,pkgs)
