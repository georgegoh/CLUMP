# $Id: kickstart.py 3425 2010-01-26 03:40:44Z yqang $
#
#   Copyright 2008 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#   
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#
#
import os
import md5crypt
import time
import string
from random import choice

from kusu.genconfig import Report
from kusu.core import database
from kusu.repoman.tools import getOS
from primitive.installtool.commands import GenerateAutoInstallScriptCommand
from primitive.support import osfamily

SUPPORTED_OS = osfamily.getOSNames('rhelfamily') + ['fedora']

def createDB():
    engine = os.getenv('KUSU_DB_ENGINE')
    if engine == 'mysql':
        dbdriver = 'mysql'
    else:
        dbdriver = 'postgres'
    dbdatabase = 'kusudb'
    dbuser = 'apache'
    dbpassword = None

    return database.DB(dbdriver, dbdatabase, dbuser, dbpassword)

class thisReport(Report):
    
    def toolHelp(self):
        print "Generates kickstart file for a nodegroup. Run via: # genconfig kickstart <ngid>"

    def getRandomSeq(self, length=8, chars=string.letters + string.digits):
        """Return a random sequence length chars long."""
        return ''.join([choice(chars) for i in range(length)])

    def runPlugin(self, pluginargs):
        """ Retrieve the required information to generate a kickstart file."""
        if not pluginargs:
            self.toolHelp()
            return
        else:
            db = createDB()
            # get the nodegroup ID.
            ngid = pluginargs[0]
            # work only if a valid nodegroup ID is given.
            valid_ng = [x.ngid for x in db.NodeGroups.select()]
            if int(ngid) not in valid_ng:
                print "Supplied <ngid> %s  not found in database." % ngid
                return
            else:
                # Retrieve NodeGroup object.
                try:
                    ng_obj = db.NodeGroups.selectfirst_by(ngid=ngid)
                except Exception, e:
                    print "Could not retrieve the NodeGroup object from database."
                    return
                # Retrieve os name, major ver, minor ver and arch.
                try:
                    os,major,minor,arch = getOS(db, ng_obj.ngname)
                    if os not in SUPPORTED_OS:
                        print "Cannot generate kickstart.cfg for unsupported OS '%s'" % os
                        return
                except Exception, e:
                    print "Could not retrieve the OS type and version."
                    return
                # Retrieve partition rules.
                try:
                    partition_rules = db.Partitions.select_by(ngid=ngid)
                except Exception, e:
                    print "Could not retrieve partition rules from database."
                    return

                # Retrieve Installation url.
                try:
                    # Get the Primary Installer's IP.
                    pi_name = db.AppGlobals.selectfirst_by(kname='PrimaryInstaller').kvalue
                    pi_nics = db.Nodes.selectfirst_by(name=pi_name).nics
                    pi_ip = filter(lambda x: x.network.type=='provision', pi_nics)[0].ip
                    # Set up the installsrc.
                    installsrc = 'http://%s/repo/%s' % (pi_ip, ng_obj.repoid)
                except Exception, e:
                    print "Could not get installation URL."
                    return

                # Retrieve network profile.
                networkprofile = {}

                try:
                    rootpw = md5crypt.md5crypt(str(self.getRandomSeq()), str(time.time()));
                except Exception, e:
                    print "Could not generate root password."
                    return
                # Retrieve timezone.
                try:
                    tz = db.AppGlobals.selectfirst_by(kname='Timezone_zone').kvalue
                except Exception, e:
                    print "Could not retrieve timezone from database."
                    return
                # Retrieve utc.
                try:
                    tz_utc = bool(db.AppGlobals.selectfirst_by(kname='Timezone_utc').kvalue)
                except Exception, e:
                    print "Could not retrieve timezone_utc from database."
                    return
                # Retrieve language.
                try:
                    lang = db.AppGlobals.selectfirst_by(kname='Language').kvalue
                except Exception, e:
                    print "Could not retrieve language from database."
                    return
                # Retrieve keyboard.
                try:
                    keyb = db.AppGlobals.selectfirst_by(kname='Keyboard').kvalue
                except Exception, e:
                    print "Could not retrieve keyboard from database."
                    return
                # Retrieve package list.
                try:
                    packages = [x.packagename for x in db.Packages.select_by(ngid=ngid)]
                    ng = db.NodeGroups.select_by(ngid=ngid)[0]
                    packages.extend([x.cname for x in ng.components if not x.kit.isOS])
                except Exception, e:
                    print "Could not retrieve package list from database."
                    return

                # If this is a new nodegroup, it may be of a different OS from the
                # master's. For HP-ICE provisioning, we need to handle lang and keyb
                # settings differently.
                if ngid > 5:
                    # Retrieve PROVISION type
                    try:
                        provision = db.AppGlobals.selectfirst_by(kname='PROVISION').kvalue
                    except Exception, e:
                        print "Could not retrieve PROVISION from database."
                        return

                    if not provision == 'KUSU':
                        # Retrieve NodeGroup object for installer.
                        try:
                            installer_ng_obj = db.NodeGroups.selectfirst_by(ngid=1)
                        except Exception, e:
                            print "Could not retrieve the installer nodeGroup object from database."
                            return
                        # Retrieve installer's os.
                        try:
                            installer_os, _, _, _ = getOS(db, installer_ng_obj.ngname)
                        except Exception, e:
                            print "Could not retrieve the OS type and version for installer."
                            return

                        # Use sane defaults if the os of the installer and the compute
                        # nodegroup differs.
                        if not installer_os.lower() == os.lower():
                            lang = 'en'
                            keyb = 'us'

            ic = GenerateAutoInstallScriptCommand(os={'name': os, 'version':major},
                                                  diskprofile=None,
                                                  partitionrules=partition_rules,
                                                  installsrc=installsrc,
                                                  networkprofile=networkprofile,
                                                  rootpw=rootpw,
                                                  tz=tz,
                                                  tz_utc=tz_utc,
                                                  lang=lang,
                                                  keyboard=keyb,
                                                  packageprofile=packages,
                                                  diskorder=[],
                                                  instnum='',
                                                  template_uri='file:///opt/kusu/etc/templates/kickstart.tmpl',
                                                  outfile='/dev/stdout')
            ic.execute()
