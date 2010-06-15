#!/usr/bin/env python
#
# $Id$
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

import sys
sys.path.append('/opt/kusu/lib/python')
from path import path

# for debugging
#import cgi
#import cgitb; cgitb.enable()

PCM_MANPATH = '/opt/kusu/man/man8'
CGI_BIN = 'get_manpage.cgi'

print "Content-Type: text/html"
print

# Get all PCM cmd manpages
manpages = path(PCM_MANPATH).files("kusu-*.8.gz")
# stripext().stripext() removes '.8.gz'
# basename() gives the filename without the directory
manpages = [ manpage.stripext().stripext().basename() for manpage in manpages ]
manpages.sort()

if not manpages:
    print 'No manpages found'
    sys.exit(1)

# Output list of OCS manpage links
print '<ul>'
for manpage in manpages:
    link = '<a href="%s?cmd=%s">%s</a>' % (CGI_BIN, manpage, manpage)
    print '<li>' + link + '</li>'
print '</ul>'

