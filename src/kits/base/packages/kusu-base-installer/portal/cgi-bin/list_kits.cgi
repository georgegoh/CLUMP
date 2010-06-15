#!/usr/bin/env python

#
# Copyright (C) 2007 Platform Computing Inc.

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

import os
import sys
import cgi
import re
# for debugging
#import cgitb; cgitb.enable()
sys.path.append('/opt/kusu/lib/python')
sys.path.append('/opt/kusu/lib64/python')
sys.path.append('/opt/primitive/lib/python2.4/site-packages')
sys.path.append('/opt/primitive/lib64/python2.4/site-packages')
from path import path
from kusu.kitops.kitops import KitOps

OCS_KITPATH = '/var/www/html/kits'
FIND = '/usr/bin/find'

def getKitDescFromKitInfo(dir_path):
    dir_path = '/'.join(dir_path[1:4])
    d = path(OCS_KITPATH)/dir_path
    kid = d.readlink().split('/')[-2]
    ko = KitOps()
    return ko.getKitDescription(kid)

print "Content-Type: text/html"
print

# Does the kits docs dir exist?
if (not os.path.exists(OCS_KITPATH) or not os.path.isdir(OCS_KITPATH)):

   OCS_KITPATH = '/srv/www/htdocs/kits'
   if (not os.path.exists(OCS_KITPATH) or not os.path.isdir(OCS_KITPATH)):
      print "Could not find kit documentation directory"
      sys.exit(1)

# Find path to index.html for all kits
cmd = 'cd %s ; %s -L . -maxdepth 3 -name index.html' % (OCS_KITPATH,FIND)
(f_out,f_in) = os.popen4(cmd)
f_out.close()

# Output links to kit docs
print '<ul>'
for line in f_in.readlines():
   path_dirs = line[:-1].split('/')
   kit = path_dirs[1]
   # Capitalize kit display name
   kit_title = kit[0].upper() + kit[1:]
   version = path_dirs[2]
   index = path_dirs[3]
   link = '<a href="../kits/%s/%s/%s" target="_blank">%s Kit</a> <span>(Version %s)</span>' % \
             (kit,version,index,kit_title,version)
   print '<li>' + link + '</li>'

# Find path to index.html for New kits
cmd = 'cd %s ; %s -L . -maxdepth 4 -mindepth 4 -name index.html' % (OCS_KITPATH,FIND)
(f_out,f_in) = os.popen4(cmd)
f_out.close()

# Output links to kit docs
for line in f_in.readlines():
   path_dirs = line[:-1].split('/')
   # path_dirs[3] is supposed to be the kit release number which should be a digit
   # only those path_dirs having correct release number will be handled
   kit_title = getKitDescFromKitInfo(path_dirs)
   if path_dirs[3].isdigit():
       kit = path_dirs[1]
       if not kit_title:
           # Capitalize kit display name
           kit_title = kit[0].upper() + kit[1:]
       version = path_dirs[2]
       kid = path_dirs[3]
       index = path_dirs[4]
       link = '<a href="../kits/%s/%s/%s/%s" target="_blank">%s</a> <span>(Version %s)</span>' % \
                 (kit,version,kid,index,kit_title,version)
       print '<li>' + link + '</li>'


print '</ul>'

f_in.close()
