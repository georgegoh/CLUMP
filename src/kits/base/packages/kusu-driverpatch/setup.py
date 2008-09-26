#!/usr/bin/env python
# $Id: setup.py 901 2008-02-27 01:54:04Z nninaba $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-driverpatch",
    version="0.2",
    author="Najib Ninaba",
    author_email="najib@osgdc.org",
    url="http://www.osgdc.org/project/kusu",
    platforms=["any"],
    packages = ['driverpatch'],
    package_dir = {'driverpatch' : 'src/lib'},
    scripts=['src/bin/driverpatch','src/bin/patchpcitable-script']
     )
