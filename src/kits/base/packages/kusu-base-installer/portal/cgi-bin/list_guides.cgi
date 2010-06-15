#!/usr/bin/env python

#
# Copyright (C) 2010 Platform Computing Inc.

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
import glob
# for debugging
#import cgitb; cgitb.enable()

sys.path.append("/opt/primitive/lib/python%s/site-packages" % sys.version[:3])
from primitive.system.software.dispatcher import Dispatcher

KIT_DOC_ROOT = Dispatcher.get('webserver_docroot') or '/var/www/html'
KIT_DOC_PATH = KIT_DOC_ROOT + '/kits'
PLATFORM_KITS=['rtm','lsf','isf-ac','hpc','mpi','cuda']

def formatKitName(kitname):
    for kit in PLATFORM_KITS:
        if kit in kitname.lower():
            if kitname.find('platform-') > 0:
                kit=kitname.split('platform-')[-1]
                kit = kit.replace('-', ' ')
            kitname = 'Platform ' + kit.upper()
            return kitname

    kitname = kitname[0].upper() + kitname[1:]
    if kitname.find('_') > 0:
        kitname = kitname.replace('_', ' ')
    return kitname

def getGuideLinkTitle(filename):
    #capitalize for each word
    words = []
    for w in filename.rsplit('.', 1)[0].split('_'):
       if w == 'platform':
           continue
       if w.upper() == 'PCM':
           words.append(w.upper())
           continue
       if w in ['user', 'guide' ]: 
           words.append(w.capitalize())
           continue
       if w in ['with', 'the', 'in', 'and', 'at', 'on', 'a']: 
           words.append(w)
           continue
       words.append(formatKitName(w))
    return ' '.join(words)

#begin HTML content
print "Content-Type: text/html"
print

installed_kits = []
#Find all kits
for kp in glob.glob('%s/*' % KIT_DOC_PATH):
    if not os.path.isdir(kp):
        continue
    kn = kp.rsplit('/', 1)[-1]
    if kn == 'base':
        #ensure the base kit is first
        installed_kits.insert(0, kn)
    else:
        installed_kits.append(kn)

if 'base' not in installed_kits:
    print "Could not find base kit"
    sys.exit(1)

# Output links to guides
print '<ul>'
for kit in installed_kits:
    #Find html/pdf guides in "$KIT_DOC_PATH/<kit>/<version>/<1>/guides" directory
    guide_paths = glob.glob('%s/%s/*/*/guides/*.html' % (KIT_DOC_PATH, kit))
    guide_paths.extend(glob.glob('%s/%s/*/*/guides/*.pdf' % (KIT_DOC_PATH, kit)))
    for guide_path in guide_paths:
        version, minor, ignore, guide_file = guide_path.rsplit('/', 4)[1:5]
        #TODO: Should add version to title when support kit with multiple versions
        link = '<a href="../kits/%s/%s/%s/guides/%s">%s</a>' % \
             (kit, version, minor, guide_file, getGuideLinkTitle(guide_file))
        print '<li>' + link + '</li>'

    #Find pdf guides in "$KIT_DOC_PATH/<kit>/<version>" directory for old kits
    for guide_path in glob.glob('%s/%s/*/*/*.pdf' % (KIT_DOC_PATH, kit)):
        version, minor, guide_file = guide_path.rsplit('/', 3)[1:4]
        link = '<a href="../kits/%s/%s/%s/%s">%s</a>' % \
             (kit, version, minor, guide_file, getGuideLinkTitle(guide_file))
        print '<li>' + link + '</li>'

print '</ul>'

