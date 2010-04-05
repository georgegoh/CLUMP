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
import urllib
import socket
# for debugging
#import cgitb; cgitb.enable()

# Globals

OCS_KITPATH = '/var/www/html/kits'
BASE_URL = 'http://localhost/cgi-bin'
LIST_MANPAGES_CGI = 'list_manpages.cgi'
LIST_HOSTINFO_CGI = 'list_hostinfo.cgi'
#LIST_KITS_CGI = 'list_kits.cgi'
#LIST_GUIDES_CGI = 'list_guides.cgi'
#LIST_USEFUL_CGI = 'list_useful.cgi'

# Helpers

def outputURL(cgi):
   url = urllib.URLopener()
   fp = url.open('%s/%s' % (BASE_URL,cgi))

   for line in fp.readlines():
      print line[:-1]
   fp.close()

def headContents():
   print '<head><title>Welcome to Kusu Desis release</title></head>'
   print '<link href="../portal/styles/portal.css" rel="stylesheet" type="text/css"/>'

def pageHeader():
   print '<table class="PageHeaderBorder">'
   print '   <tr>'
   print '   <td><img src="../portal/images/logo.jpg" height="80" width="180" style="margin:0px 20px"/></td>'
   print '   <td class="PageHeaderCell">'
   outputURL(LIST_HOSTINFO_CGI)
   print '   </td>'
   print '   </tr>'
   print '</table>'

def pageTOC():
   print '<table class="TOC">'
   print '<tr><td>'
   print '<span class="title2">Table of Contents:</span><br/>'
   #print '<a href="#Useful_Links">Useful Links</a><br/>'
   #print '<a href="#Installed_Kits">Installed Kits</a><br/>'
   #print '<a href="#Guides">Guides</a><br/>'
   print '<a href="#PCM_Tools_Man_Pages">Kusu Tools Man Pages</a><br/>'
   print '</td></tr>'
   print '</table>'
   print '<br/>'

def sectionHeader(header):
   print '<a name="%s"/>' % header.replace(' ', '_')
   print '<table class="SectionHeaderBorder">'
   print '<tr><td class="SectionHeaderCell">'
   print header + '<br/>'
   print '</td></tr>'
   print '</table>'

def sectionFooter():
   print '<a href="#Top">Back to Top</a><br/>'
   print '<br/>'

def startHTML():
   print "<html>"

def endHTML():
   print "</html>"

def startBody():
   print "<body>"

def endBody():
   print "</body>"




# Output HTML

print "Content-Type: text/html"
print

startHTML()
headContents()

startBody()
pageHeader()
pageTOC()

# List manpage links
sectionHeader('PCM Tools Man Pages')
print '<p>Refer to the following man pages for detailed command-line usage:</p>'
outputURL(LIST_MANPAGES_CGI)
sectionFooter()

# The links below are PCM-related and commented out for kusu development. 

# List useful links
#sectionHeader('Useful links')
#print '<p>A collection of links to web GUIs of installed applications and support sites:</p>'
#outputURL(LIST_USEFUL_CGI)
#sectionFooter()

# List kit links
#sectionHeader('Installed Kits')
#print '<p>The following kits are available on this cluster:</p>'
#outputURL(LIST_KITS_CGI)
#sectionFooter()

# List guide links
#sectionHeader('Guides')
#print '<p>Refer to the following guides for detailed instructions:</p>'
#outputURL(LIST_GUIDES_CGI)
#sectionFooter()

endBody()
endHTML()

