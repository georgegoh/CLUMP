#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: setup.py 443 2010-01-28 08:02:52Z mike $
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-uat",
    version="0.2",
    author="Mike Mazur",
    author_email="mmazur@osgdc.org",
    url="http://www.osgdc.org/project/kusu",
    platforms=["any"],
    packages=['uat'],
    package_dir={'uat':'src/lib'},
    scripts=[]
     )
