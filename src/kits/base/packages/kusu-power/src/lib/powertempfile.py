#!/usr/bin/python
#-*- coding: utf-8 -*-
#
# $Id: powertempfile.py 3126 2009-10-20 07:29:26Z abuck $
#
# Module --------------------------------------------------------------------
#
# $RCSfile$
#
# COPYRIGHT NOTICE
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See COPYING for details.
#
# CREATED
#   Author: rk
#   Date:   2003/11/14
#
# LAST CHANGED
#   $Author: kbjornst $
#   $Date: 2008-11-25 06:07:03 -0500 (Tue, 25 Nov 2008) $
#
# ---------------------------------------------------------------------------

"""
Module of conveniant handeling of temporary files and directories
"""

import random
import string
import tempfile
import os
import shutil

def _randomString(length=8):
    """Generate a random string of length length"""
    s = ''
    for _i in range(length):
        s += random.choice(string.digits + string.ascii_letters)
    return s

def mkstemp(suffix="", prefix=tempfile.gettempprefix(), directory=tempfile.gettempdir()):
    """Open a temporary file"""
    filename = os.path.join(directory, prefix+str(os.getpid()) + _randomString() + suffix)
    fd = os.open(filename, os.O_EXCL|os.O_CREAT|os.O_RDWR, 0700)
    return (fd, filename)

class tmpdir:
    """
    Class for temporary directories with unique names

    The directory is created in class-constructor, and removed in destructor.
    caller is responsible of removing any content _inside_ the directory so
    it can be successfully removed
    """
    def __init__(self, suffix="", prefix=tempfile.gettempprefix(), directory=tempfile.gettempdir()):
        self.dirname = os.path.join(directory, prefix + str(os.getpid()) + _randomString() + suffix)
        os.mkdir(self.dirname)
    def __del__(self):
        shutil.rmtree(self.dirname)
    def getDirname(self):
        """
        Get the name of the temporary directory
        """
        return self.dirname



class NamedTemporaryFile:
    """
    Class for temporary files with unique names

    Unlike TemporaryFile theese tmpfiles have directory-entries
    """
    def __init__(self, mode='w+b', bufsize=-1, suffix="", prefix="powertemp", directory=tempfile.gettempdir()):
        (self.fd, self.name) = mkstemp(suffix, prefix, directory)
        fileobject = os.fdopen(self.fd, mode)
        self.write = fileobject.write
        self.writelines = fileobject.writelines
        self.read = fileobject.read
        self.readlines = fileobject.readlines
        self.seek = fileobject.seek
        self.close = fileobject.close
        self.flush = fileobject.flush
        self.fileno = fileobject.fileno
    def __del__(self):
        os.remove(self.name)
