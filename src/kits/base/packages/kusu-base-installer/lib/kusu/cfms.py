#!/usr/bin/python

# $Id$

# cfms.py - The Cluster File Management Server library 

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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#

import os
import sys
import string
import glob
import pwd
import grp
from stat import *

from kusu.kusudb import KusuDB
from kusu.cfmnet import CFMNet
import ipfun 

class PackBuilder:
    """This class contains the code for generating the packaged files for
    distribution through CFM. """


    def __init__(self):
        """__init__ - initializer for the class"""
        self.db          = KusuDB()
        self.database    = 'kusudb'
        self.user        = 'apache'
        self.password    = ''
        self.cfmbasedir  = '/opt/kusu/cfm'
        self.origdir     = '/etc/cfm'
        self.md5sum      = '/usr/bin/md5sum'
        self.passwdfile  = '/opt/kusu/etc/db.passwd'   # Change this later
        self.nodegrplst  = {}    # Dictionary of the nodegroups and their ID's
        self.pkgfile     = '/opt/kusu/etc/package.lst'  # File holding package list
        self.updatesize  = 0      # The size of the files that need to be updated
        self.db.connect(self.database, self.user)
        tmp = self.db.getAppglobals('CFMBaseDir')
        if tmp:
            self.cfmbasedir = tmp
        if not os.path.exists(self.md5sum):
            raise "Fix the PATH for md5sum!"

        try:
            self.apacheuser  = pwd.getpwnam('apache')
        except:
            raise "Apache is not installed!  Fix this!"

        # Populate the list of nodegroups
        query = ('select ngname, ngid from nodegroups')

        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            self.errorMessage('DB_Query_Error\n')
            sys.exit(-1)
                 
        if data:
            for line in data:
                name, ngid = line
                self.nodegrplst[name] = ngid


    def __getNodeNameFromNGID(self, ngid):
        """__getNodeNameFromNGID - Get the name of the node group from the
        NGID."""
        for key in self.nodegrplst.keys():
            if self.nodegrplst[key] == ngid:
                return key
        return ""
    
        

    def __getNumNodes(self):
        """__getNumNodes - Returns a count of the number of nodes in the cluster."""
        query = ('select count(*) from nodes')
        try:
            self.db.execute(query)
            data = self.db.fetchone()
        except:
            self.errorMessage('DB_Query_Error\n')
            sys.exit(-1)
                 
        if data:
            return data[0]
        return 0
    

    def __getInstallers(self):
        """getInstallers - Get a list of all of the available installer IP's"""
        query = ('select nics.ip from nics, nodes, nodegroups where '
                 'nodegroups.ngid=nodes.ngid and nodes.nid=nics.nid '
                 'and nodegroups.ngname="Installer"')
        installers = []
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            self.errorMessage('DB_Query_Error\n')
            sys.exit(-1)
                 
        if data:
            for line in data:
                installers.append(line[0])

        return installers
                

    def __getBroadcasts(self):
        """getBroadcasts - Get a list of all of the available netowk broadcast addresses"""
        query = ('select network, subnet from networks')

        bc = []
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            self.errorMessage('DB_Query_Error\n')
            sys.exit(-1)
                 
        if data:
            for line in data:
                ip, sb = line
                bc.append(ipfun.getBroadcast(ip, sb))

        return bc


    def __getFileInfo(self,cfmfile):
        """__getFileInfo - Returns a tupple containing the filename,
        username, groupname, mode, mtime and md5sum of the original
        file (not the one if the cfmdir)."""
        
        # self.origdir
        # Strip off the self.cfmbasedir, and ngid, and replace it with the
        # self.origdir, and node group name
        f = cfmfile[len(self.cfmbasedir):]
        ngid = string.split(f, '/')[1]
        top = "%s/%i" % (self.cfmbasedir, ngid)
        origtop = "%s/%s" % (self.origdir, self.__getNodeNameFromNGID(ngid))
        file = "%s/%s" % (origtop, cfmfile[len(top):])

        attr = os.stat(file)
        mtime = attr[ST_MTIME]
        mode = S_IMODE(attr[ST_MODE])

        try:
            user = pwd.getpwuid(attr[ST_UID])[0]
        except:
            user = 'nobody'

        try:
            group = grp.getgrgid(attr[ST_GID])[0]
        except:
            group = 'nobody'

        cmd = '%s "%s"' % (self.md5sum, file)
        md5sum = '-none-'
        for line in os.popen(cmd).readlines():
            bits = string.split(line)
            if bits[1] == fqfn:
                md5sum = bits[0]

        retval = (file, user, group, mode, mtime, md5sum)
        return retval

        
    def genFileList(self):
        """__genFileList - Generate the cfmfiles.lst file.  This file contains a list
        of all the files managed by the CFM. """
        filename = os.path.join(self.cfmbasedir, 'cfmfiles.lst')
        filep = open(filename, 'w')
        
        # Find the directories for the node groups 
        for nodegrp in self.nodegrplst.keys():
            ngid = self.nodegrplst[nodegrp]
            # top = os.path.join(self.cfmbasedir, '%i' % ngid)
            top = "%s/%i" % (self.cfmbasedir, ngid)
            for root, dirs, files in os.walk(top):
                if not files:
                    continue
                for file in files:
                    fqfn, user, group, mode, mtime, md5sum = self.__getFileInfo(file)
                    filep.write('%s %s %s %s %i %s\n' % (fqfn, user, group, mode, mtime, md5sum))
        filep.close()
        os.chown(filename, self.apacheuser[2], self.apacheuser[3])
                        


    def updateCFMdir(self):
        """updateCFMdir -  scan through the origdir looking for modified
        files to manage.  When one is found process it for distribution.
        This method will return the size of the update."""

        pattern = os.path.join(self.origdir, '*')
        flist = glob.glob(pattern)
        if len(flist) == 0:
            # Odd!
            return

        self.updatefiles = []
        self.updatesize  = 0

        # Find the directories for the node groups 
        for nodegrp in self.nodegrplst.keys():
            ngid = self.nodegrplst[nodegrp]
            top = os.path.join(self.origdir, nodegrp)
            # cfmloc = os.path.join(self.cfmbasedir, "%i" % ngid)  # THIS DOES NOT WORK!
            cfmloc = "%s/%i/" % (self.cfmbasedir, ngid)
            
            if not os.path.exists(top):
                continue

            for root, dirs, files in os.walk(top):
                if not files:
                    continue
                for file in files:
                    fqfn = os.path.join(root, file)
                    origmtime = os.path.getmtime(fqfn)
                    # cfmfqfn = os.path.join(cfmloc, fqfn[len(top):]) # THIS DOES NOT WORK!
                    cfmfqfn = "%s%s" % (cfmloc, fqfn[len(top):])
                    cfmmtime = 0

                    if not os.path.exists(cfmfqfn):
                        print "New file found:  %s" % fqfn
                    else:
                        cfmmtime = os.path.getmtime(cfmfqfn)

                    # Only deal with newer files
                    if origmtime > cfmmtime:
                        # Compress, encrypt, and base64 encode
                        cmd = 'gzip -c \"%s\" |openssl bf -e -a -salt -pass file:/opt/kusu/etc/db.passwd -out %s' % (fqfn, cfmfqfn)

                        # Encode:
                        #  openssl bf -e -a -salt -in infile -out infile.bf
                        # Decode:
                        #  openssl bf -d -a -salt -in infile.bf -out infile

                        if not os.path.exists(os.path.dirname(cfmfqfn)):
                            os.system('mkdir -p \"%s\"' % os.path.dirname(cfmfqfn))
                            os.system('chown -R apache \"%s\"' % cfmloc)

                        for line in os.popen(cmd).readlines():
                            if line:
                                print "ERROR:  %s" % line

                        self.updatesize = self.updatesize + os.path.getsize(cfmfqfn)
                        os.chown(cfmfqfn, self.apacheuser[2], self.apacheuser[3])

        return self.updatesize


    def getPackageList(self, nodegroup=''):
        """__getPackageList - Update the list of packages the node groups
        should have installed."""
        grplst = []
        
        if not nodegroup:
            grplst = self.nodegrplst.keys()
        else:
            grplst.append(nodegroup)
            try:
                ngid = self.nodegrplst[nodegrp]
            except:
                grplst = self.nodegrplst.keys()

        for nodegrp in grplst:
            packages = []
            ngid = self.nodegrplst[nodegrp]
            # Add the packages
            query = ('select packagename from packages where ngid="%s"' % ngid)

            try:
                self.db.execute(query)
                data = self.db.fetchall()
            except:
                self.errorMessage('DB_Query_Error\n')
                sys.exit(-1)
                 
            if data:
                for p in data:
                    packages.append(p[0])
                    # print "Adding Package %s" % p[0]
                    
            # Add the components
            query = ('select components.cname from components, ng_has_comp '
                     'where components.cid=ng_has_comp.cid and ngid="%s"' % ngid)

            try:
                self.db.execute(query)
                data = self.db.fetchall()
            except:
                self.errorMessage('DB_Query_Error\n')
                sys.exit(-1)
                 
            if data:
                for p in data:
                    packages.append(p[0])

            # Make the node group directory if necessary
            if not os.path.exists(os.path.join(self.cfmbasedir, "%i" % ngid)):
                os.system('mkdir -p \"%s/%i\"' % (self.cfmbasedir, ngid))
                os.system('chown -R apache \"%s\"' % self.cfmbasedir)

            # Now check the file to see if there are actually any changes needed
            # pfile = os.path.join(self.cfmbasedir, "%i" % ngid, self.pkgfile)  # DOES NOT WORK!
            pfile = "%s/%i/%s" % (self.cfmbasedir, ngid, self.pkgfile)

            if not packages:
                if os.path.exists(pfile):
                    # Remove the file contents
                    filep = open(pfile, 'w')
                    filep.close()
                continue

            packages.sort()

            # Test to see if the package list is unchanged
            oldlist= []
            try:
                filep = open(pfile, 'r')
                data = filep.readlines()
                filep.close()
                for l in data:
                    if l[0] != '#':
                        oldlist.append(l)

                oldlist.sort()
            except:
                pass
            
            if oldlist == packages:
                # Do nothing!
                continue

            # The package list has changed.  Output the new list
            if not os.path.exists(os.path.dirname(pfile)):
                os.system('mkdir -p \"%s\"' % os.path.dirname(pfile))
                
            filep = open(pfile, 'w')
            filep.write('# Generated automatically.  Do not Edit!\n')
            filep.write(string.join(packages, '\n'))
            filep.close()
            os.chown(pfile, self.apacheuser[2], self.apacheuser[3])


    def signalUpdate(self, type, nodegroup=''):
        """signalUpdate - Send the update message to the cluster, or node group"""

        installers = self.__getInstallers()
        broadcasts = self.__getBroadcasts()
        if nodegroup:
            try:
                ngid = self.nodegrplst[nodegroup]
            except:
                ngid = 0
        else:
            ngid = 0

        # Calculate waittime
        numnodes = self.__getNumNodes()
        wait = 10
        if self.updatesize:
            wait = self.updatesize * numodes * 8 / (50000000)

        cfmnet = CFMNet()
        cfmnet.sendPacket(installers, broadcasts, type, ngid, wait)


if __name__ == '__main__':
    pb = PackBuilder()
    pb.getPackageList()
    pb.updateCFMdir()
    pb.genFileList()
    pb.signalUpdate(3, '')
