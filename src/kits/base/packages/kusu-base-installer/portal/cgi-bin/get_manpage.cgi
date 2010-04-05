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
import re
import cgi
# for debugging
#import cgitb; cgitb.enable()

OCS_MANPATH = '/opt/kusu/man/man8'
GUNZIP = '/bin/gunzip'
NROFF = '/usr/bin/nroff'
COL = '/usr/bin/col'

print "Content-Type: text/html"
print

form = cgi.FieldStorage()
try:
   cmd_obj = form['cmd']
except:
   print "No command given"
   sys.exit(1)

cmd = cmd_obj.value

# Does cmd have legal filename characters? We don't want 
# arbitrary strings to be passed in...
if (len(cmd) == 0 or not re.match('^[.A-Za-z0-9_-]+$',cmd)):
   print "Command given has illegal characters"
   sys.exit(1)

# Does manpage for cmd exist?
cmd_manpage = "%s/%s.8.gz" % (OCS_MANPATH,cmd)
if (not os.path.exists(cmd_manpage)):
   print "No manpage found for command: %s" % cmd
   sys.exit(1)

# Grab text from manpage
os_cmd = '%s < %s | %s -c -man | %s -b' % (GUNZIP,cmd_manpage,NROFF,COL)
(f_out,f_in) = os.popen4(os_cmd)
f_out.close()


# Output HTML
print '<pre>'
for line in f_in.readlines():
   print cgi.escape(line[:-1])
print '</pre>'

f_in.close()

