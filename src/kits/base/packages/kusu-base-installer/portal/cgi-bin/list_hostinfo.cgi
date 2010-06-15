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
import socket
# for debugging
#import cgitb; cgitb.enable()

REDHAT_RELEASE = '/etc/redhat-release'
SLES_RELEASE = '/etc/SuSE-release'
KUSU_RELEASE = '/etc/kusu-release' 
OCSGUI_URL='http://%s:8080/platform' % os.uname()[1]
HPC_Community_URL='http://www.hpccommunity.org'

def addOCSGUILink():
    if (os.path.exists('/usr/bin/pmcadmin')):
        print '<span class="title">PCM Web GUI:</span>'
        print "<a href='%s' target='_blank'>" % OCSGUI_URL.replace('hostname',server)
        print '%s' % OCSGUI_URL.replace('hostname',server)
        print '</a>'
	print '<br/>'


def getLineFromFile(file):
   if (os.path.exists(file)):
      f = open(file)
      line = f.readline()[:-1]
      if (line == ''):
         line = 'Unknown'
      f.close()
      return line

   return 'Unknown'


print "Content-Type: text/html"
print

server = socket.gethostname()
os_version = getLineFromFile(REDHAT_RELEASE)
if os_version == 'Unknown':
    os_version = getLineFromFile(SLES_RELEASE)
kusu_version= getLineFromFile(KUSU_RELEASE)

print '<span class="title">Hostname:</span> ' + server + '<br/>'
print '<span class="title">PCM Version:</span> ' + kusu_version + '<br/>'
print '<span class="title">OS Version:</span> ' + os_version + '<br/>'

addOCSGUILink()

