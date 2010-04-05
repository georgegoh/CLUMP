#!/usr/bin/env python

#
# Copyright (C) 2009 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
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
KUSU_RELEASE = '/etc/kusu-release' 
OCSGUI_URL='http://%s:8080/platform' % os.uname()[1]
NTOPGUI_URL='http://%s:3000' % os.uname()[1]
GANGGUI_URL='http://%s/ganglia/' % os.uname()[1]
RTMGUI_URL='http://%s/cacti/' % os.uname()[1]
NAGIOSGUI_URL='http://%s/nagios/' % os.uname()[1]
HPC_Community_URL='http://www.hpccommunity.org'
MYPLATFORM='http://my.platform.com'

sys.path.append('/opt/primitive/lib/python2.4/site-packages')
from primitive.system.software.dispatcher import Dispatcher
WEBSERVER_CONFDIR = Dispatcher.get('webserver_confdir')
WEBSERVER_DOCROOT = Dispatcher.get('webserver_docroot')

def addOCSGUILink():
    if (os.path.exists('/usr/bin/pmcadmin')):
        print '<span">PCM Web GUI:</span>'
        print "<a href='%s' target='_blank'>" % OCSGUI_URL
        print '%s' % OCSGUI_URL
        print '</a>'
        print '<br/>'

def addNTOPGUILink():
    if (os.path.exists('/etc/init.d/ntop')):
        print '<span>NTOP Web GUI:</span>'
        print "<a href='%s' target='_blank'>" % NTOPGUI_URL
        print '%s' % NTOPGUI_URL
        print '</a>'
        print '<br/>'

def addNAGIOSGUILink():
    if (grep_for_RPM('component-nagios-support') and not os.path.exists('/opt/repository')):
        print '<span>Nagios Web GUI:</span>'
        print "<a href='%s' target='_blank'>" % NAGIOSGUI_URL
        print '%s' % NAGIOSGUI_URL
        print '</a>'
        print '<br/>'

def addGANGLIAGUILink():
    if (os.path.exists('%s/ganglia.conf' % WEBSERVER_CONFDIR) or \
            os.path.exists('%s/ganglia' % WEBSERVER_DOCROOT)):
        print '<span>Ganglia Web GUI:</span>'
        print "<a href='%s' target='_blank'>" % GANGGUI_URL
        print '%s' % GANGGUI_URL
        print '</a>'
        print '<br/>'

def addRTMLink():
    if (grep_for_RPM('component-rtm-master') and os.path.exists('/etc/rtm-release')):
        print '<span>RTM Web GUI:</span>'
        print "<a href='%s' target='_blank'>" % RTMGUI_URL
        print '%s' % RTMGUI_URL
        print '</a>'
        print '<br/>'

def grep_for_RPM(grep_for):
    """
    Checks whether any RPMs matching `grep_for` are installed.

    Returns True if a match is found, False otherwise.
    """

    exit_code = os.system('rpm -qa | grep %s > /dev/null' % grep_for)
    return 0 == exit_code

print "Content-Type: text/html"
print

addOCSGUILink()
addNTOPGUILink()
addNAGIOSGUILink()
addGANGLIAGUILink()
addRTMLink()
print '<span>Kusu community web site:</span>'
print '<a href="' + HPC_Community_URL + '" target="_blank">' + HPC_Community_URL + '</a><br/>'
print '<span>PCM web site:</span>'
print '<a href="' + MYPLATFORM + '" target="_blank">' + MYPLATFORM + '</a><br/>'

