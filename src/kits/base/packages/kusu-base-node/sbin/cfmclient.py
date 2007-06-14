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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#

# NOTE:  The cfmclient runs on nodes that do not have the complete
#        kusu/lib.  Do not use libraries that are unavailable on the
#        compute nodes.

UPDATEFILE    = 1
UPDATEPACKAGE = 2

import os
import sys
import string
import pwd
import grp
import urllib
import random
from kusu.ipfun import *

class Merger:
    """ The Merger Class is responsible for dealing with merging
    different types of files."""

    def __init__(self):
        pass

    def mergeFile(self, filename):
        """mergeFile - This function is for merging the group, password,
        and shadow files.  It will involve a lot of work"""

        osfile   = "/opt/kusu/etc/cfm/%s.OS" % filename
        t0file   = "/opt/kusu/etc/cfm/%s.T0" % filename
        apndfile = "%s.append" % filename
        
        # Make the original file if it does not exist.
        if not os.path.exists(osfile):
            os.system('mkdir -p \"%s\"' % os.path.dirname(osfile))
            os.system('cp \"%s\" \"%s\"' % (filename, osfile))

        # Which file are we dealing with
        if filename == '/etc/group':
            # Check for changes in the local file first
            added, removed = self.__checkLineChanges(filename, t0file)

            # Merge the changes into the OS file
            # Remove the lines that have been locally removed 
            for line in removed:
                key = string.split(line, ':')[0]
                self.__removeSelectedLine(osfile, key, ':')

            # Add in the lines that that are local
            self.__addLines(osfile, added)
            
            # Merge the OS file and append file
            os.system('cat \"%s\" \"%s\" > \"%s\"' % (osfile, apndfile, filename))
            os.unlink(apndfile)

            # Make a copy of the file for checking for changes
            os.system('cp \"%s\" \"%s\"' % (filename, t0file))

        elif filename == '/etc/passwd':
            # Merge the password file
            print "Merging passwd"
            # Check for changes in the local file first
            added, removed = self.__checkLineChanges(filename, t0file)

            # Merge the changes into the OS file
            # Remove the lines that have been locally removed 
            for line in removed:
                key = string.split(line, ':')[0]
                self.__removeSelectedLine(osfile, key, ':')

            # Add in the lines that that are local
            self.__addLines(osfile, added)
            
            # Merge the OS file and append file
            os.system('cat \"%s\" \"%s\" > \"%s\"' % (osfile, apndfile, filename))
            os.unlink(apndfile)

            # Make a copy of the file for checking for changes
            os.system('cp \"%s\" \"%s\"' % (filename, t0file))

        elif filename == '/etc/shadow':
            # Merge the shadow file
            print "Merging shadow"
            # Check for changes in the local file first
            added, removed = self.__checkLineChanges(filename, t0file)

            # Merge the changes into the OS file
            # Remove the lines that have been locally removed 
            for line in removed:
                key = string.split(line, ':')[0]
                self.__removeSelectedLine(osfile, key, ':')

            # Add in the lines that that are local
            self.__addLines(osfile, added)

            # Remove the password entry for root from the OS file 
            self.__removeSelectedLine(osfile, 'root', ':')
            
            # Merge the OS file and append file
            os.system('cat \"%s\" \"%s\" > \"%s\"' % (osfile, apndfile, filename))
            os.unlink(apndfile)

            # Make a copy of the file for checking for changes
            os.system('cp \"%s\" \"%s\"' % (filename, t0file))
        else:
            print "WARNING:  Unhandled file merge for file:  %s.  Ignoring" % filename 


    def __checkLineChanges(self, origfile, t0file):
        """__checkLinesChanges - Examine the original, and time=0 file for
        added and removed lines.  Return a list of the added and removed lines.
        """
        added = []
        removed = []
        if not os.path.exists(t0file):
            return [[], []]

        infiledata = []
        fin = open(origfile, 'r')
        for line in fin.readlines():
            if line[0] == '#':
                continue
            if line:
                infiledata.append(line)
        fin.close()
        
        t0filedata = []
        fout = open(t0file, 'r')
        for line in fout.readlines():
            if line[0] == '#':
                continue
            if line:
                infiledata.append(line)
        fout.close()

        # Scan through the infiledata removing any entries that appear in the t0filedata
        inf = infiledata[:]   # Need to work with a copy to prevent weirdness
        for line in inf:
            if line in t0filedata:
                t0filedata.remove(line)
                infiledata.remove(line)

        # Anything left in infiledata has been added locally by the user
        # Anything left in the t0data has been removed locally by the user
        return [infiledata, t0filedata]
        

    def __removeSelectedLine(self, filename, key, seperator):
        """removeSelectedLine - Search through a file removing the line that
        starts with the key, and is seperated by seperator."""
        tmpfile = "%s.tmp" % filename
        try:
            fin  = open(filename, 'r')
            fout = open(tmpfile, 'w')
            for line in fin.readlines():
                bits = string.split(line, seperator)
                if bits[0] != key:
                    fout.writeline(line)
                
            fin.close()
            fout.close()
            os.rename(tmpfile, filename)
        except:
            print "Failed to remove localy removed lines from %s / %s" % (filename, tmpfile)


    def __addLines(self, filename, newlines):
        """__addLines - Add the newlines to the specified file."""
        try:
            fout = open(filename, 'a')
        except:
            print "Failed to open: %s for appending" % filename
            return
        
        for line in newlines:
            outline = "%s\n" % line
            fpout.writeline(outline)

        fout.close()



class CFMClient:

    def __init__(self, argv):
        self.args        = argv
        self.CFMBaseDir  = ''
        self.ostype      = ''
        self.ngid        = 0
        self.repoid      = 0
        self.pkglstpost  = 'package.lst'
        self.packagelst  = '/opt/kusu/etc/package.lst'
        self.cfmfilelst  = '/opt/kusu/etc/cfmfiles.lst'
        self.newpackages = []    # List of packages to add
        self.oldpackages = []    # List of packages to remove
        self.newfiles    = []    # List of new filesto update
        self.md5sum      = '/usr/bin/md5sum'
        self.type   = 0
        self.installers = []
        self.bestinstaller = ''   # The IP of the installer to get files from

    
    def parseargs(self):
        """parseargs - Parse the command line arguments and populate the
        class variables"""

        # This tool is not for use by the user
        args = self.args[1:]
        i = 0
        while i < len(args):
            if args[i] == '-t':
                if len(args) > (i+1):
                    val = args[i+1]
                    i += 1
                    try:
                        self.type = string.atoi(val)
                    except:
                        print "ERROR:  Invalid type argument"
                        sys.exit(1)
                else:
                    print "ERROR:  Type not specified"
                    sys.exit(2)
                    
            elif args[i] == '-i':
                if len(args) > (i+1):
                    self.installers = string.split(args[i+1])
                    i += 1
                else:
                    print "ERROR:  Installers not specified"
                    sys.exit(3)
            else:
                print "ERROR:  Unknown argument"
                sys.exit(4)
            i += 1


    def getProfileVal(self, name):
        """getProfileVal - Returns the value of the NII property from
        /etc/profile.nii with any quotes removed."""
        cmd = "grep %s /etc/profile.nii" % name
        val = ''
        for line in os.popen(cmd).readlines():
            loc = string.find(line, name)
            if loc < 0:
                continue

            t2 = string.split(line[string.find(line, '=')+1:])[0]
            val = string.strip(t2, '"')
            break
        return val


    def setupNIIVars(self):
        """setupNIIVars - Read in the needed variables from the profile.nii"""
        self.CFMBaseDir = self.getProfileVal("CFMBaseDir")
        self.ostype     = self.getProfileVal("NII_OSTYPE")
        val             = self.getProfileVal("NII_REPO")
        if val:
            self.repoid = os.path.basename(val)
        try:
            self.ngid = string.atoi(self.getProfileVal("NII_NGID"))
        except:
            print "ERROR:  Unable to determine NGID.  Got: %s" % self.ngid
            self.ngid = 0
        
            

    def __haveLocalAccess(self):
        """__haveLocalAccess - This function will determine if the CFMBaseDir is
        mounted locally.  Returns True if it is available.  This will look for the
        profile.nii, then try to get the CFMBaseDir from it, then see if it has
        the $CFMBaseDir/$NGID/opt/kusu/etc/package.lst
        If local directory access is not available it will find an installer to
        use from the installer list and set self.bestinstaller."""

        if not self.CFMBaseDir:
            self.CFMBaseDir = self.getProfileVal("CFMBaseDir")

        # Test for local access
        filetest = "%s/%s/opt/kusu/etc/package.lst" % (self.CFMBaseDir, self.ngid)
        # print "++  Testing for: %s" % filetest
        # print "++  CFMBaseDir: %s" % self.CFMBaseDir
        # print "++  NGID = %i" % self.ngid
        if os.path.exists(filetest):
            return True

        myIPs = getMyIPs()
        # print "myIPs = %s, installers = %s" % (myIPs, self.installers)
        bestIPlist = bestIP(myIPs, self.installers)
        # print "BestIPlist = %s" % bestIPlist
        if len(bestIPlist) == 0:
            # No good one found!
            bestIPlist = self.installers[:]
            
        self.bestinstaller = bestIPlist[random.randint(0, len(bestIPlist)-1)]
        return False


    def __setFilePerms (self, file, username, grpname, mode):
        """__setFilePerms - Set the file ownership, group, and mode of a file.
        The user and group are the names, not UID/GID's.  This is to allow
        this to work across OS's.  If the username, or grpname cannot be
        determined then "nobody" will be used."""

        try:
            uid = pwd.getpwnam(username)[2]
        except:
            uid = pwd.getpwnam('nobody')[2]

        try:
            gid = grp.getgrnam(username)[2]
        except:
            gid = grp.getgrnam('nobody')[2]

        try:
            os.chmod(file, mode)
        except:
            print "ERROR:  Failed to set the mode of %s to %s" % (file, mode)
            sys.exit(-1)
            
        try:
            os.chown(file, uid, gid)
        except:
            print "ERROR:  Failed to set the ownership of %s, UID=%s, GID=%s" % (file, uid, gid)



    def __getFile (self, source, deststruct, cfmfile=0):
        """__getFile - Copy, or download a file to a given location.
        The source is the fully qualified path without the CFMBaseDir and
        NGID.  The __getFile will work out the correct path/URL to get
        it from.  The deststruct is a tupple containing:
        (filename, user, group, mode, md5sum(optional))
        If the decrypt flag is set to 1 it will decrypt the file. 
        If the cfmfile flag is set to 1, then the source path will not
        use the ngid.  This is needed to get cfmfiles.lst, and package.lst
        These files are not encrypted."""

        # This is an intermediate file we will use
        tmpfile = "%s.CFMtmpFile" % deststruct[0]
        
        if self.__haveLocalAccess():
            print "++  Have local access"
            # Copy the file from a directory
            if cfmfile:
                cfmpath = "%s/%s" % (self.CFMBaseDir, source)
            else:
                cfmpath = "%s/%i/%s" % (self.CFMBaseDir, self.ngid, source)
            if not os.path.exists(cfmpath):
                print "ERROR: Unable to locate: %s" % cfmpath
                return

            os.system('cp \"%s\" \"%s\" > /tmp/m3 2>&1' % (cfmpath, tmpfile))

        else:
            print "++  No local access"
            # Copy the file from one of the installers.  Make the URL
            if cfmfile:
                url = "http://%s/cfm/%s" % (self.bestinstaller, source)
            else:
                url = "http://%s/cfm/%s/%s" % (self.bestinstaller, self.ngid, source)
            datafile = ''
            print "URL = %s" % url
            try:
                (datafile, header) = urllib.urlretrieve(url, tmpfile)
            except:
                print "Download 1 Failed!"
                # Download failed.  Try the other IP's
                for ip in self.installers:
                    if cfmfile:
                        url = "http://%s/cfm/%s" % (ip, source)
                    else:
                        url = "http://%s/cfm/%s/%s" % (ip, self.ngid, source)
                    try:
                        (datafile, header) = urllib.urlretrieve(url, tmpfile)
                        # This one worked.  Switch to it
                        self.bestinstaller = ip[:]
                        break
                    except:
                        pass
                if not datafile:
                    print "ERROR:  Failed to download: %s" % url
                    return

        # Decrypt and decompress the file (if needed)
        if not cfmfile:
            tmpfile2 = "%s.decrypted.CFMtmpFile" % deststruct[0]
            # *** Really need a better shared secret
            cmd = 'openssl bf -d -a -salt -pass file:/opt/kusu/etc/db.passwd -in %s |gunzip > "%s"' % (tmpfile, tmpfile2)
            print "Running: %s" % cmd
            for line in os.popen(cmd).readlines():
                if line:
                    print "ERROR:  %s" % line
                    if os.path.exists(tmpfile2):
                        os.unlink(tmpfile2)
                    if os.path.exists(tmpfile):
                        os.unlink(tmpfile)
                    return
            print "tmpfile2=%s  tmpfile=%s" % (tmpfile2, tmpfile)
            os.rename(tmpfile2, tmpfile)

        # Set the file permissions
        # print "Calling __setFilePerms('%s', '%s', '%s', '%s')" % (tmpfile, deststruct[1], deststruct[2], deststruct[3])
        self.__setFilePerms(tmpfile, deststruct[1], deststruct[2], deststruct[3])

        # If an md5sum is provided test the file.
        try:
            origmd5sum = deststruct[4]
            cmd = '%s "%s"' % (self.md5sum, tmpfile)
            md5sum = '-none-'
            for line in os.popen(cmd).readlines():
                bits = string.split(line)
                md5sum = bits[0]
                if origmd5sum != md5sum:
                    print "ERROR:  The checksum of the received file, and the original do not match.  Aborting transfer!"
                    print "Filename = %s" % tmpfile
                    print "origmd5sum= %s   md5sum= %s" % (origmd5sum, md5sum)
                    os.unlink(tmpfile)
                    return

        except:
            # No md5sum provided
            pass
        
        os.rename(tmpfile, deststruct[0])


    def __setupForYum(self):
        """__setupForYum  - Make a yum.conf pointing to the installer that is closest"""
        dirname = 'Redhat'
        if self.ostype[:6] == 'fedora':
            dirname = 'Fedora'
        if self.ostype[:4] == 'rhel' :
            dirname = 'Redhat'
        if self.ostype[:6] == 'centos':
            dirname = 'CentOS'

        yumconf = '/tmp/yum.conf'
        fp = file(yumconf, 'w')
        out = ( '[main]\n'
                'cachedir=/var/cache/yum\n'
                'debuglevel=2\n'
                'logfile=/var/log/yum.log\n'
                'reposdir=/dev/null\n'
                'tolerant=1\n\n'
                '[base]\n'
                'name=%s - Base\n'
                'baseurl=http://%s/repos/%s/%s/RPMS/\n' % (self.ostype, self.bestinstaller, self.repoid, dirname)
                )

        fp.write(out)
        fp.close()
        
        
    def __installPackages(self):
        """__installPackages - Install the packages in the list."""

        if not self.newpackages:
            print "Nothing to add"
            return
        
        if self.ostype[:6] == 'fedora' or self.ostype[:4] == 'rhel' or self.ostype[:6] == 'centos':
            self.__setupForYum()
            cmd = "/usr/bin/yum -y install "
            for i in self.newpackages:
                cmd += "%s " % i

            print "Running:  %s" % cmd
            #for line in os.popen(cmd).readlines():
            #    print line


    def __removePackages(self):
        """__removePackages - Remove the packages in the list."""

        if not self.oldpackages:
            print "Nothing to remove"
            return
        
        if self.ostype[:6] == 'fedora' or self.ostype[:4] == 'rhel' or self.ostype[:6] == 'centos':
            self.__setupForYum()
            cmd = "/usr/bin/yum -y remove "
            for i in self.oldpackages:
                cmd = "/usr/bin/yum -y remove %s" % i

                print "Running:  %s" % cmd
                #for line in os.popen(cmd).readlines():
                #    print line


    def __getFileEntries(self, filename):
        """__getFileEntries - Return the contents of a file as a list.  Comments
        are stripped."""
        retval = []
        
        try:
            filep = open(filename, 'r')
        except:
            return retval
        while True:
                
            line = filep.readline()
            if len(line) == 0:
                break
            if line and line[0] != '#':
                retval.append(string.strip(line))
                    
        filep.close()
        return retval


    def __getPackageChanges(self):
        """__getPackageChanges - Populate the old and new lists of packages."""
        oldfile = '%s.ORIG' % self.packagelst
        oldlist = self.__getFileEntries(oldfile)
        newlist = self.__getFileEntries(self.packagelst)

        # Scan over the newlist and oldlist for entries removing those in both
        tmp = newlist[:]
        for entry in tmp:
            if entry in oldlist:
                oldlist.remove(entry)
                newlist.remove(entry)

        # Anything still in newlist is a new package
        self.newpackages = []
        for entry in newlist:
            if entry:
                self.newpackages.append(entry)
            #print "Found new package: %s" % entry

        # Anything still in oldlist is a package to remove
        self.oldpackages = []
        for entry in oldlist:
            if entry:
                self.oldpackages.append(entry)
            # print "Found old package: %s" % entry


    def __processFileName(self, filename):
        """__processFileName - The filename from the cfmfile list contains
        additional information on how the file should be treated.  This
        function returns a tupple with:  "proper filename", "action"
        The action will be ignore if it is from another node group."""

        # Determine is any special processing is needed
        action = ''
        if filename[-7:] == '.append':
            action = 'append'
        if filename[-6:] == '.merge':
            action = 'merge'

        fn = filename
        if action:
            fn = filename[:-(len(action) + 1)]
        else:
            fn = filename

        # Test to see if this is in the same node group
        ng = string.atoi(string.split(fn[(len(self.CFMBaseDir)):], '/')[1])
        if ng != self.ngid:
            action = 'ignore'

        # Now strip off the leading CFMBaseDir, and NGID
        fn = fn[(len(self.CFMBaseDir) + len("%i" % self.ngid) + 1):]

        return (fn, action)


    def __findOlderFiles(self):
        """__findOlderFiles  - This function will read the cfmfilelst, and
        locate files in that list that are older than the timestamp in the
        file, then populate the self.newfiles with the list of files to
        update."""
        try:
            filep = open(self.cfmfilelst, 'r')

        except:
            print "ERROR:  Could not open: %s" % self.cfmfilelst
            return
        
        for line in filep.readlines():
            if line[0] == '#':
                continue
            if line:
                # /opt/kusu/cfm/5/opt/kusu/etc/package.lst apache apache 420 1181168668 8c1a2bb5be7c8a4c8279484772fccf01
                chunks = string.split(line)
                md5sum = chunks[-1:][0]
                time   = chunks[-2:-1][0]
                tmode  = chunks[-3:-2][0]
                group  = chunks[-4:-3][0]
                user   = chunks[-5:-4][0]
                filen  = string.join(chunks[:-5], ' ')
                filename, action = self.__processFileName(filen)

                # print "__findOlderFiles:  filen=%s, filename=%s" % (filen, filename)
                # print "__findOlderFiles:  user=%s, group=%s, mode=%s" % (user, group, mode)
                # print "__findOlderFiles:  md5sum=%s" % md5sum
                
                if action == 'ignore':
                    continue

                # Make mode an octal number
                mode = string.atoi(tmode, 8)
                    
                # Test to see if it's newer
                if os.path.exists(filename):
                    mtime = os.path.getmtime(filename)

                else:
                    print "NOTICE:  File: %s does not exist!" % filename
                    mtime = 0

                if mtime < time:
                    # File needs to be updated
                    self.newfiles.append([filename, user, group, mode, action, md5sum])
                    
        filep.close()
                                         

    def __installNewFiles(self):
        """__installNewFiles - Install the files in the  self.newfiles list"""
        for filename, user, group, mode, action, md5sum in self.newfiles:

            attr = (filename, user, group, mode, md5sum)
            print "Getting file: %s" % filename
            self.__getFile(filename, attr, 0)
            
            # Determine what to do based on the action
            if action == '':
                continue
            elif action == 'append':
                realfile = filename[:-(len(action) + 1)]
                osfile   = "/opt/kusu/etc/%s.OS" % realfile
                if not os.path.exists(osfile):
                    os.system('mkdir -p \"%s\"' % os.path.dirname(osfile))
                    os.system('cp \"%s\" \"%s\"' % (realfile, osfile))
                os.system('cat \"%s\" \"%s\" > \"%s\"' % (osfile, filename, realfile))
                os.unlink(filename)
            elif action == 'merge':
                # This is for the group passwd, and shadow files.
                merger = Merger()
                merger.mergeFile(realfile)
            else:
                print "WARNING: Unknown action type: %s for %s" % (filename, action) 
        

    def updatePackages (self):
        """updatepackages - Update packages"""
        print "Updating Packages"
        if os.path.exists(self.packagelst):
            os.rename(self.packagelst, '%s.ORIG' % self.packagelst)
        attr = (self.packagelst, 'root', 'root', 0600)
        self.__getFile('%i.%s' % (self.ngid, self.pkglstpost), attr, 1)

        # Test the package file to see if it is valid
        testdata = self.__getFileEntries(self.packagelst)
        if testdata[0][0] == '<':
            # This is not proper content
            print "ERROR:  Failed to get the package.lst."
            if os.path.exists('%s.ORIG' % self.packagelst):
                os.rename('%s.ORIG' % self.packagelst, self.packagelst)
        else:
            self.__getPackageChanges()
            self.__removePackages()
            self.__installPackages()
            if os.path.exists('%s.ORIG' % self.packagelst):
                os.unlink('%s.ORIG' % self.packagelst)
        

    def updateFiles (self):
        """updatefiles - Update files"""
        print "Updating Files"
        # Update the package list.
        attr = (self.cfmfilelst, 'root', 'root', 0600)
        self.__getFile('cfmfiles.lst', attr, 1)
        self.__findOlderFiles()
        self.__installNewFiles()


    def run (self):
        """run - Entry point for CFM client"""
        self.parseargs()
        self.setupNIIVars()
        global UPDATEFILE
        global UPDATEPACKAGE
        print "Update type: %i" % self.type
        print "Installers: %s" % self.installers
        if not self.installers or not self.type:
            print "Usage:  {cmd} -t [1|2|3] -i {Installer list}"
            sys.exit(-1)
            
        if self.type & UPDATEFILE:
            self.updateFiles()

        if self.type & UPDATEPACKAGE:
            self.updatePackages()

        print "Done"
        sys.exit(0)


    def tester(self):
        """tester - Just an entry point for testing the methods"""
        print "Testing"

        
            
if __name__ == '__main__':
    app = CFMClient(sys.argv)
    if app.getProfileVal('NII_NGID') == "":
        print "ERROR:  Unable to locate /profile.nii"
    
    app.run()
