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

from kusu.core.db import KusuDB
from kusu.cfmnet import CFMNet
from kusu.ipfun import *

CFMFILE='/etc/cfm/.cfmsecret'

# Change this when the plugins are relocated
PLUGINS='/opt/kusu/lib/plugins/cfmsync'

class PackBuilder:
    """This class contains the code for generating the packaged files for
    distribution through CFM. """


    def __init__(self, stderrtxt, stdouttxt):
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
        self.pkgfile     = 'package.lst'  # File holding package list
        self.updatesize  = 0      # The size of the files that need to be updated
        self.cfmdirfiles = []     # List of all files that should be in CFM distrib dir
        self.stdoutMessage = stdouttxt
        self.errorMessage = stderrtxt
        self.db.connect(self.database, self.user)
        tmp = self.db.getAppglobals('CFMBaseDir')
        if tmp:
            self.cfmbasedir = tmp
        if not os.path.exists(self.md5sum):
            self.errorMessage('cfm_Failed to locate md5sum\n')
            sys.exit(1)

        try:
            self.apacheuser  = pwd.getpwnam('apache')
        except:
            self.errorMessage('cfm_No_apache_user\n')
            sys.exit(1)

        # Populate the list of nodegroups
        query = ('select ngname, ngid from nodegroups')

        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            self.errorMessage('DB_Query_Error: %s\n', query)
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
            self.errorMessage('DB_Query_Error: %s\n', query)
            sys.exit(-1)
                 
        if data:
            return data[0]
        return 0
    

    def __getInstallers(self):
        """getInstallers - Get a list of all of the available installer IP's"""
        query = ('select nics.ip from nics, nodes, nodegroups, networks where '
                 'nodegroups.ngid=nodes.ngid and nodes.nid=nics.nid and '
                 'networks.netid=nics.netid and networks.usingdhcp=0 '
                 'and nodegroups.type="installer" and networks.type="provision"')
        installers = []
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            self.errorMessage('DB_Query_Error: %s\n', query)
            sys.exit(-1)
                 
        if data:
            for line in data:
                installers.append(line[0])

        return installers
                

    def __getBroadcasts(self):
        """getBroadcasts - Get a list of all of the available netowk broadcast addresses"""
        query = ('select distinct network, subnet from networks where type="provision" and usingdhcp=0')

        bc = []
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            self.errorMessage('DB_Query_Error: %s\n', query)
            sys.exit(-1)
                 
        if data:
            for line in data:
                ip, sb = line
                bc.append(getBroadcast(ip, sb))

        return bc


    def __getFileInfo(self,cfmfile):
        """__getFileInfo - Returns a tupple containing the filename,
        username, groupname, mode, mtime and md5sum of the original
        file (not the one if the cfmdir)."""
        
        # self.origdir
        # Strip off the self.cfmbasedir, and ngid, and replace it with the
        # self.origdir, and node group name
        f = cfmfile[len(self.cfmbasedir):]
        ngid = string.atoi(string.split(f, '/')[1])
        top = "%s/%i" % (self.cfmbasedir, ngid)
        origtop = "%s/%s" % (self.origdir, self.__getNodeNameFromNGID(ngid))
        file = "%s%s" % (origtop, cfmfile[len(top):])
        #print "cfmfile=>%s<, f=>%s<" % (cfmfile, f)
        #print "top=%s" % top
        #print "cfmfile[len(top):]=%s" % cfmfile[len(top):]
        #print "file=%s" % file
        #print "ngid=%s Node Group = >%s<" % (ngid, self.__getNodeNameFromNGID(ngid))
        #print "self.origdir=%s" % self.origdir
        #print "origtop=%s" % origtop
        
        if not os.path.exists(file):
            # This is a special file.  It does not exist in the /etc/cfm dir.
            file = cfmfile

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

        cmd = '%s \"%s\"' % (self.md5sum, file)
        md5sum = '-none-'
        for line in os.popen(cmd).readlines():
            bits = string.split(line)
            if bits[1] == file[:len(bits[1])]:
                md5sum = bits[0]

        retval = (cfmfile, user, group, mode, mtime, md5sum)
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
                    fn = "%s/%s" % (root, file)
                    fqfn, user, group, mode, mtime, md5sum = self.__getFileInfo(fn)
                    filep.write('%s %s %s %o %i %s\n' % (fqfn, user, group, mode, mtime, md5sum))
        filep.close()
        os.chown(filename, self.apacheuser[2], self.apacheuser[3])
                        

    def removeOldFiles(self):
        """removeOldFiles - Use the existing cfmfiles.lst and the self.cfmdirfiles to
        determine which files are no longer needed in hte CFM distribution directory
        and delete them"""
        filename = os.path.join(self.cfmbasedir, 'cfmfiles.lst')
        if not os.path.exists(filename):
            return
        
        filep = open(filename, 'r')
        oldfileentries = []
        for line in filep.readlines():
            if line[0] == '#':
                continue
            chunks = string.split(line)
            filen  = string.join(chunks[:-5], ' ')
            if filen != '':
                oldfileentries.append(filen)

        filep.close()
        
        if len(self.cfmdirfiles) == 0:
            return
            
        # Strip out the duplicates
        for fname in self.cfmdirfiles:
            if fname in oldfileentries:
                oldfileentries.remove(fname)

        if len(oldfileentries) > 0:
            for fname in oldfileentries:
                if os.path.exists(fname):
                    self.stdoutMessage('cfm_Removing old file: %s\n', fname)
                    try:
                        os.unlink(fname)
                    except:
                        pass


    def updateCFMdir(self):
        """updateCFMdir -  scan through the origdir looking for modified
        files to manage.  When one is found process it for distribution.
        This method will return the size of the update."""

        # Call the plugins to generate any dynamic config files
        # This is to support "getent" and other tools like it.
        global PLUGINS
        sys.path.append(PLUGINS)
        flist = glob.glob('%s/*' % PLUGINS)
        if len(flist) != 0:
            flist.sort()
            for plugin in flist:
                self.stdoutMessage('cfm_Running plugin:  %s\n', plugin)
                os.system('/bin/sh %s >/dev/null 2>&1' % plugin)
        
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
            cfmloc = "%s/%i" % (self.cfmbasedir, ngid)
            
            if not os.path.exists(top):
                continue

            for root, dirs, files in os.walk(top):
                if not files:
                    continue
                for file in files:
                    fqfn = os.path.join(root, file)
                    if not os.path.exists(fqfn):
                        if os.path.islink(fqfn):
                            self.errorMessage('cfm_broken_symbolic_link: %s\n', fqfn)
                        continue
                    origmtime = os.path.getmtime(fqfn)
                    # cfmfqfn = os.path.join(cfmloc, fqfn[len(top):]) # THIS DOES NOT WORK!
                    cfmfqfn = "%s%s" % (cfmloc, fqfn[len(top):])
                    cfmmtime = 0

                    if not os.path.exists(cfmfqfn):
                        self.stdoutMessage('cfm_New file found:  %s\n', fqfn)
                    else:
                        cfmmtime = os.path.getmtime(cfmfqfn)

                    self.cfmdirfiles.append(cfmfqfn)

                    # Only deal with newer files
                    if origmtime > cfmmtime:
                        # Compress, encrypt, and base64 encode
                        global CFMFILE
                        if os.path.exists(CFMFILE):
                            cmd = 'gzip -c \"%s\" |openssl bf -e -a -salt -pass file:%s -out %s' % (fqfn, CFMFILE, cfmfqfn)
                        else:
                            # Fail back for older code
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
                                self.errorMessage('cfm_error: %s\n', line)

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
                self.errorMessage('DB_Query_Error: %s\n', query)
                sys.exit(-1)
                 
            if data:
                for p in data:
                    packages.append(p[0])
                    
            # Add the components
            query = ('select components.cname from components, ng_has_comp '
                     'where components.cid=ng_has_comp.cid and ngid="%s"' % ngid)

            try:
                self.db.execute(query)
                data = self.db.fetchall()
            except:
                self.errorMessage('DB_Query_Error: %s\n', query)
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
            pfile = "%s/%i.%s" % (self.cfmbasedir, ngid, self.pkgfile)

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

            # Strip out duplicates
            tmplst = packages[:]
            for i in xrange(1, len(tmplst)):
                if tmplst[i-1] == tmplst[i]:
                    packages.remove(tmplst[i])
            
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
            wait = self.updatesize * numnodes * 8 / (50000000)

        cfmnet = CFMNet()
        cfmnet.sendPacket(installers, broadcasts, type, ngid, wait)


if __name__ == '__main__':
    app = UpdateApp(sys.argv)
    _ = app.langinit()
    pb = PackBuilder(app.errorMessage, app.stdoutMessage)
    pb.getPackageList()
    pb.updateCFMdir()
    pb.removeOldFiles()
    pb.genFileList()
    pb.signalUpdate(3, '')
