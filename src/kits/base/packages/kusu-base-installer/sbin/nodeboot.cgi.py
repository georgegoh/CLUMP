#!/usr/bin/python
#
# $Id$
#
#   Copyright 2007 Platform Computing Inc
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
#
#

# This can be run by Apache, so be careful about paths!
# NOTE:  Do not use mod_python.  See:
#   http://www.modpython.org/FAQ/faqw.py?req=show&file=faq02.013.htp
# for why not.

import os
import sys
import string
import cgi
import time

sys.path.append("/opt/kusu/bin")
sys.path.append("/opt/kusu/lib")
sys.path.append("/opt/kusu/lib/python")

from optparse import OptionParser
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB


class NodeInfo:
    """This class will provide the functions for getting the Node Installation
    Information, and for setting the database fields for a node """

    def __init__(self, user='nobody'):
        """__init__ - initializer for the class"""
        self.db = KusuDB()
        self.db.connect('kusudb', user)

        
    def getNIInfo(self, nodename, nodeip):
        """getNII - Generates the Node Installation Information for a given
        node."""
        if not nodename:
            return

        # Create the nodeinfo line
        query = ('select repos.installers, repos.repository, repos.ostype, '
                 'nodegroups.ngid, nodegroups.installtype, nodes.nid from nodes, '
                 'nodegroups, repos where nodes.ngid=nodegroups.ngid and '
                 'nodegroups.repoid=repos.repoid and nodes.name="%s"' % nodename)
        try:
            self.db.execute(query)
            data = self.db.fetchone()
        except:
            # Return 500
            sys.exit(-1)
        if not data:
            # Need to trigger a 500 error
            sys.exit(-1)
        installer, repo, os, ngid, type, nid = data
        index = repo.splitall().index('repos')
        repo = os.path.sep.join(repo.splitall()[index:])
            
        #FIXME: WORK IN PROGRESS
        # Currently just use the ip from the master installer, where the 
        # network request from the node is hitting. 
        # We will use multiple installers next time when
        # we have other installers up and running. 
        query = ('select ip from nics,nodes where nics.nid=nodes.nid ' + 
                 'and nodes.name=(select kvalue from appglobals where kname="PrimaryInstaller") ' + 
                 'and netid = (select netid from nodes,nics where nodes.nid=nics.nid and nodes.name="%s" and nics.ip="%s")' % (nodename,nodeip))

        try:
            self.db.execute(query)
            data = self.db.fetchone()
        except:
            # Return 500
            sys.exit(-1)
        if not data:
            # Need to trigger a 500 error
            sys.exit(-1)
 
        installer = data[0]        
        print '<nodeinfo name="%s" installers="%s" repo="%s" ostype="%s" installtype="%s" nodegrpid="%i">' % (nodename, installer, repo, os or '', type, ngid)

        # NICinfo section
        query = ('select nics.ip, networks.usingdhcp, networks.network, '
                 'networks.subnet, networks.device, networks.suffix, '
                 'networks.gateway, networks.options, nics.boot '
                 'from nics,networks where networks.netid=nics.netid '
                 'and nics.nid="%i"' % nid)
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            # Return 500
            print "Oops! again"
            sys.exit(-1)
        if not data:
            # Need to trigger a 500 error
            print "Oops!"
            sys.exit(-1)
        for row in data:
            ip, dhcp, network, subnet, dev, suffix, gw, opt, boot = row
            print '    <nicinfo device="%s" ip="%s" subnet="%s" network="%s" suffix="%s" gateway="%s" dhcp="%s" options="%s" boot="%s"></nicinfo>' % (dev, ip, subnet, network, suffix, gw, dhcp, opt, boot)

        # Partition Info
        query = ('select device, partition, mntpnt, fstype, size, options, preserve '
                 'from partitions where ngid="%i"' % ngid )
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            # Return 500
            print "Oops! again 3"
            sys.exit(-1)
        if data:
            for row in data:
                device, partition, mntpnt, fstype, size, options, preserve = row
                print '    <partition device="%s" partition="%s" mntpnt="%s" fstype="%s" size="%s" options="%s" preserve="%s"></partition>' % (device, partition, mntpnt or '', fstype or '', size, options or '', preserve)

        # Component Info
        query = ('select components.cname from components, kits, ng_has_comp '
                 'where components.cid=ng_has_comp.cid and '
                 'kits.kid=components.kid and kits.isOS=0 and '
                 'ng_has_comp.ngid="%i"' % ngid )
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            # Return 500
            print "Oops! again 3"
            sys.exit(-1)
        if data:
            for row in data:
                cname = row[0]
                print '    <component>%s</component>' % cname

        # Optional packages
        query = ('select packagename from packages '
                 'where ngid="%i"' % ngid )
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            # Return 500
            print "Oops! again 4"
            sys.exit(-1)
        if data:
            for row in data:
                pack = row[0]
                print '    <optpackage>%s</optpackage>' % pack

        # Optional scripts
        query = ('select script from scripts '
                 'where ngid="%i"' % ngid )
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            # Return 500
            print "Oops! again 5"
            sys.exit(-1)
        if data:
            for row in data:
                script = row[0]
                print '    <optscript>%s</optscript>' % script

        # Appglobals 
        query = ('select kname, kvalue from appglobals where '
                 'ngid is NULL or ngid="%i"' % ngid )
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            # Return 500
            print "Oops! again 6"
            sys.exit(-1)
        if data:
            for row in data:
                kname, kvalue = row
                print '    <appglobals name="%s" value="%s"></appglobals>' % (kname, kvalue or '') 

        print '</nodeinfo>'



    def getCFMfile(self):
        """getCFMfile - Displays the contents of the Cluster File Management (CFM)
        change file."""
        cfmdir = self.db.getAppglobals('CFMBaseDir')
        if not cfmdir:
            return
        cfmfile = os.path.join(cfmdir, 'cfmfiles.lst')
        if os.path.exists(cfmfile):
            print '<cfm>'
            print "CFMBaseDir=%s" % cfmdir
            try:
                fp = file(cfmfile, 'r')
                while True:
                    line = fp.readline()
                    if len(line) == 0:
                        break
                    sys.stdout.write(line)
            except:
                pass
            print '</cfm>'
            fp.close()


    def getNodeName(self, nodename='', nodeip=''):
        """getNodeName - returns the name of the node given the IP, or name."""
        if nodename:
            return nodename

        if not nodeip:
            return
        
        query = ('select nodes.name from nodes,nics where '
                 'nodes.nid = nics.nid and nics.ip = "%s"' % nodeip)
        try:
            self.db.execute(query)

        except:
            # Return 500
            sys.exit(-1)

        data = self.db.fetchone()
        if not data:
            # Need to trigger a 404 error, but don't see how.
            print "Cannot find host for IP: %s" % nodeip

        return data[0]

        
    def setNodeInfo(self, nodename, state, bootfrom, timestamp):
        """setState - Set the nodes state in the database.  One method is
        used to reduce the DB calls."""
        if not state and bootfrom == -1 and not timestamp:
            return

        cmdstr = 'update nodes set'
        if state:
            cmdstr = cmdstr + ' state="%s",' % state
        if bootfrom != -1:
            cmdstr = cmdstr + ' bootfrom=%i,' % bootfrom
        if timestamp:
            cmdstr = cmdstr + ' lastupdate="%s",' % timestamp
        query = cmdstr[:-1] + ' where name="%s"' % nodename

        try:
            self.db.execute(query)

        except:
            # Return 500 (hopefully)
            print "Query problem:  %s" % query
            sys.exit(-1)
                 

    def regenPXE(self, nodename):
        """regenPXE - Calls the boothost tool to cause the PXE file to be
        regenerated.
        NOTE:  This forces the database connection to close! """
        self.db.disconnect()
        if os.path.exists('/opt/kusu/sbin/boothost.py'):
            os.system('/opt/kusu/sbin/boothost.py -n %s' % nodename)



class NodeBootApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)


    def toolVersion(self):
        """toolVersion - provide a version screen for this tool."""
        self.errorMessage("Version %s\n", self.version)
        sys.exit(0)


    def parseargs(self):
        """parseargs - Parse the command line arguments and populate the
        class variables"""
        
        self.parser.add_option("-v", "--version", action="store",
                               type="string", dest="getversion")
        self.parser.add_option("-d", "--displaynii", action="store_true",
                               dest="getnii", default=False)
        self.parser.add_option("-f", "--displaycfm", action="store_true",
                               dest="getcfm", default=False)
        self.parser.add_option("-i", "--nodeip", action="store",
                               type="string", dest="nodeip")
        self.parser.add_option("-n", "--nodename", action="store",
                               type="string", dest="nodename")
        self.parser.add_option("-s", "--state", action="store",
                               type="string", dest="nodestate")
        self.parser.add_option("-b", "--bootfrom", action="store",
                               type="string", dest="bootfrom")

        (self.options, self.args) = self.parser.parse_args(sys.argv)

            

    def run(self):
        """run - Run the application"""
        self.parseargs()
        node        = ''
        ip          = ''
        dumpnii     = 0
        dumpcfm     = 0
        state       = ''
        bootfrom    = -1        # -1 means unchanged, 0=network, 1=disk
        updatepxe   = 0
        timestamp   = ''        # The timestamp to go in the nodes table
        runascgi    = 0         # Flag to indicate this is running as a CGI 
        
        # Test to see if we are running as a CGI
        if os.environ.has_key('REMOTE_ADDR'):
            runascgi = 1
            
            # Prepare the CGI class
            self.cgi = cgi.FieldStorage()
            
            if os.environ.has_key('REMOTE_HOST'):
                node = os.environ['REMOTE_HOST']
            else:
                ip = os.environ['REMOTE_ADDR']

            if self.cgi.has_key('dump'):
                if self.cgi['dump'].value[0] == '1':
                    dumpnii = 1

            if self.cgi.has_key('getindex'):
                if self.cgi['getindex'].value[0] == '1':
                    dumpcfm = 1

            if self.cgi.has_key('state'):
                if self.cgi['state'].value:
                    state = self.cgi['state'].value[:19]

            if self.cgi.has_key('boot'):
                if self.cgi['boot'].value[0] == 'd':
                    bootfrom = 1
                else:
                    bootfrom = 0

        else:
            # Not running as a CGI
            if self.options.getversion:
                self.errorMessage("Version %s\n", self.version)
                sys.exit(0)
            else:
                # We need the nodes name for any of the following operations
                if self.options.nodename:
                    node = self.options.nodename
                else:
                    if self.options.nodeip:
                        ip = self.options.nodeip
                    else:
                        self.errorMessage('nodeboot_no_hostname_or_ip\n')
                        sys.exit(-1)

                if self.options.getnii:
                    dumpnii = 1
                if self.options.getcfm:
                    dumpcfm = 1
                if self.options.nodestate:
                    state = self.options.nodestate[:19]
                if self.options.bootfrom:
                    if self.options.bootfrom == 'disk':
                        bootfrom = 1
                    else:
                        bootfrom = 0
                    

        # The data should now be ready to call the methods
        if runascgi:
            print 'Content-type: text/html\n'

        #if self.cgi.has_key('dump'):
        print '<?xml version="1.0"?>'
        print "<nii>"
        print "<debug>"
        print "Dump NII: %s " % dumpnii
        print "State: %s " % state
        print "Dump CFM: %s " % dumpcfm
            
        
        # Test to see if we need write access to the database and connect 
        if bootfrom or state:
            nodefun = NodeInfo('apache')
            updatepxe = 1
        else:
            nodefun = NodeInfo()

        if not node:
            node = nodefun.getNodeName('', ip)

        print "Node: %s " % node
        print "</debug>"
        
        if dumpnii:
            nodefun.getNIInfo(node, ip)

        if dumpcfm:
            nodefun.getCFMfile()
            ltime = time.localtime(time.time())
            timestamp = "%s/%s/%s %s:%s:%s" % (ltime[0], ltime[1],
                                               ltime[2], ltime[3],
                                               ltime[4], ltime[5])

        print "</nii>"
        
        # Update State, bootfrom, and timestamp  (Methods check validity)
        nodefun.setNodeInfo(node, state, bootfrom, timestamp)
        
        # Update PXE file if needed
        if updatepxe:
            nodefun.regenPXE(node)

        
        
if __name__ == '__main__':
    app = NodeBootApp()
    app.run()
    sys.exit(0)
