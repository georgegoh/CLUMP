#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import sys
import platform
if platform.machine() == "x86_64":
    sys.path.append("/opt/kusu/lib64/python")
sys.path.append("/opt/kusu/lib/python")

from kusu.core.db import KusuDB

from path import path
from Cheetah.Template import Template
import os

 
db = KusuDB()
db.connect('kusudb', 'apache')
db.execute('select rname, version, arch, rdesc from kits order by rname, version, arch')
data = db.fetchall()           
print Template(file='/var/www/html/index.tmpl', searchList=[{'kits':data}])
