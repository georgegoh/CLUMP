#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This module deals with build operations for kits. """

from path import path
from kusu.util.errors import FileDoesNotExistError
from kusu.buildkit import kitsource

class BuildProfile(object):
    """ This class contains kit-specific profile for building kits. """
    
    def __init__(self):
        """docstring for __init__"""
        pass
        
class PackageProfile(object):
    """ This class contains package-specific profile for building packages. """
    name = None             # refers to the name of this profile
    version = None          # version string
    dirname = None          # name of unpacked directory of the package
    packagetype = None      
    buildroot = None        # refers to the install root dir when building the package
    builddir = None         # refers to the build dir for holding the building transients
    installroot = None      # refers to the real installation root path
    
    def __init__(self, name, filepath=None, version=None, buildroot=None, builddir=None, installroot=None):
        self.filepath = filepath
        self.buildroot = buildroot
        self.builddir = builddir
        self.installroot = installroot
        self.name = name
        self.version = version
        
    def setfilepath(self, value):
        """docstring for setfilepath"""
        if not value: return
        filepath = path(value)
        if not filepath.exists(): raise FileDoesNotExistError
        self._filepath = filepath
        self.dirname = path(kitsource.getDirName(filepath)).basename()
        
    def getfilepath(self):
        return self._filepath
        
    filepath = property(getfilepath,setfilepath)
    