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
from path import path

from kusu.core.db import KusuDB
from kusu.cfmnet import CFMNet
from kusu.ipfun import *

from primitive.system.software.dispatcher import Dispatcher

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
            apache = Dispatcher.get('webserver_usergroup')[0]
            self.apacheuser = pwd.getpwnam(apache)
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

    def __isFileAuthScheme(self):
        """
        Returns True if we are using file-based authentication scheme.
        """
        query = """
          SELECT * FROM appglobals 
          WHERE kname='KusuAuthScheme' AND 
                kvalue='files'
        """
        count = 0
        try:
            self.db.execute(query)
            count = self.db.rowcount
        except:
            self.errorMessage('DB_Query_Error: %s\n', query)
            sys.exit(-1)

        return count == 1
                 
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
                 'networks.netid=nics.netid and networks.usingdhcp=False '
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
        """getBroadcasts - Get a list of all of the available network broadcast addresses"""
        query = ('select distinct network, subnet from networks where type="provision" and usingdhcp=False')

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
        """__getFileInfo - Returns a tuple containing the filename,
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

    def genMergeFiles(self):
        """
        Generates /etc/cfm/group.merge, /etc/cfm/passwd.merge and /etc/cfm/shadow.merge
        by comparing the current file (e.g. /etc/group) against a version of it that was
        previously saved (e.g. /etc/cfm/group.OS). These .merge files are distributed 
        to the nodes to be merged by cfmclient.py.
        """
        for f in ["group", "passwd", "shadow"]:
            curr_file = path('/etc/%s' % f)
            os_file = path('%s/%s.OS' % (self.origdir, f))
            merge_file = path('%s/%s.merge' % (self.origdir, f))

            # For the unlikely case where the .merge file was removed by some user
            if not merge_file.exists():
                merge_file.touch()
                merge_file.chmod(0400)

            # If the saved OS copy does not exist, 
            # 1. Make a copy from the current file, keeping same file permissions
            # 2. Remove the entry for 'root' user in the OS copy for shadow
            #    i.e. /etc/cfm/shadow.OS
            # 3. Ensure that the .merge file is empty since we are starting from
            #    scratch.
            if not os_file.exists():
                curr_file.copy2(os_file)
                os_file.chmod(0400)

                if f == 'shadow':
                    # Remove root user entry
                    entries = [entry for entry in os_file.lines() \
                            if not entry.split(':')[0] == 'root']
                    os_file.write_lines(entries)

                if merge_file.text():
                    # Empty it
                    merge_file.write_text('')

                # We're done here for this file.
                continue

            # Compare contents of cur_file with os_file using set operations.
            # In this case we handle the case where lines were added to the
            # curr_file. The (orig - curr) case where lines are removed from the
            # curr_file (when compared to os_file) is not handled.
            curr = set(curr_file.lines())
            orig = set(os_file.lines())
            diff = curr - orig

            # Remove any comments in the difference
            diff = [line for line in diff if not line[0] == '#']

            if f == 'group':
                # Remove system groups (i.e. gid < 500) from the diff
                # Sample line: "video:x:33:"
                diff = [line for line in diff if not int(line.split(':')[2]) < 500]

            # Only update the .merge file if the difference has changed
            if not set(merge_file.lines()) == diff:
                merge_file.write_lines(diff)

        
    def genFileList(self):
        """
        Generates the cfmfiles.lst file.  This file contains a list
        of all the files managed by the CFM. 
        """
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
                    if file in ['passwd.merge', 'shadow.merge', 'group.merge'] and \
                            not self.__isFileAuthScheme():
                        # Skip these special merge files since we are not using
                        # file-based authentication.
                        continue
                    fn = "%s/%s" % (root, file)
                    fqfn, user, group, mode, mtime, md5sum = self.__getFileInfo(fn)
                    filep.write('%s %s %s %o %i %s\n' % (fqfn, user, group, mode, mtime, md5sum))
        filep.close()
        os.chown(filename, self.apacheuser[2], self.apacheuser[3])
                        

    def removeOldFiles(self):
        """removeOldFiles - Use the existing cfmfiles.lst and the self.cfmdirfiles to
        determine which files are no longer needed in the CFM distribution directory
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
                            cmd = 'gzip -c \"%s\" |openssl bf -e -a -salt -pass file:%s -out \"%s\"' % (fqfn, CFMFILE, cfmfqfn)
                        else:
                            # Fail back for older code
                            cmd = 'gzip -c \"%s\" |openssl bf -e -a -salt -pass file:/opt/kusu/etc/db.passwd -out \"%s\"' % (fqfn, cfmfqfn)

                        # Encode:
                        #  openssl bf -e -a -salt -in infile -out infile.bf
                        # Decode:
                        #  openssl bf -d -a -salt -in infile.bf -out infile

                        if not os.path.exists(os.path.dirname(cfmfqfn)):
                            os.system('mkdir -p \"%s\"' % os.path.dirname(cfmfqfn))
                            os.system('chown -R %s \"%s\"' % (self.apacheuser[2], cfmloc))

                        for line in os.popen(cmd).readlines():
                            if line:
                                self.errorMessage('cfm_error: %s\n', line)

                        self.updatesize = self.updatesize + os.path.getsize(cfmfqfn)
                        os.chown(cfmfqfn, self.apacheuser[2], self.apacheuser[3])

        return self.updatesize


    def getPackageList(self, nodegroup=''):
        """__getPackageList - Update the list of packages the node groups
        should have installed."""
        
        if not nodegroup or not nodegroup in self.nodegrplst:
            # If the nodegroup is not specified or invalid, iterate
            # through all nodegroups
            grplst = self.nodegrplst
        else:
            # Build a single item dict for the specified nodegroup
            grplst = { nodegroup: self.nodegrplst[nodegroup] }

        for nodegrp, ngid in grplst.iteritems():
            # Add the packages
            query = ('select packagename from packages where ngid="%s"' % ngid)

            try:
                self.db.execute(query)
                data = self.db.fetchall()
            except:
                self.errorMessage('DB_Query_Error: %s\n', query)
                sys.exit(-1)
                 
            packages = [ p[0] for p in data ]
                    
            # Add the components
            query = ('select components.cname from components, ng_has_comp '
                     'where components.cid=ng_has_comp.cid and ngid="%s"' % ngid)

            try:
                self.db.execute(query)
                data = self.db.fetchall()
            except:
                self.errorMessage('DB_Query_Error: %s\n', query)
                sys.exit(-1)
                 
            packages += [ p[0] for p in data ]

            # Make the node group directory if necessary
            if not os.path.exists(os.path.join(self.cfmbasedir, "%i" % ngid)):
                os.system('mkdir -p \"%s/%i\"' % (self.cfmbasedir, ngid))
                os.system('chown -R %s \"%s\"' % (self.apacheuser[2], self.cfmbasedir))

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
    from kusu.core import app 
    kApp = app.KusuApp()
    _ = kApp.langinit()
    pb = PackBuilder(kApp.errorMessage, kApp.stdoutMessage)
    pb.genMergeFiles()
    pb.getPackageList()
    pb.updateCFMdir()
    pb.removeOldFiles()
    pb.genFileList()
    pb.signalUpdate(3, '')
