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
FORCEFILES    = 4
UPDATEREPO    = 8

# Set DEBUG to 1 to see debugging info in /var/log/kusu/cfmclient.log
DEBUG = 1

import os
import sys
import string
import pwd
import grp
import urllib
import random
import glob
import subprocess
from kusu.ipfun import *
import tempfile
from path import path
import atexit
import time

# Add primitive to the python path. This is needed for cfmd to spawn
# cfmclient child processes properly since we are going to import
# primitive modules in cfmclient.py. Currently cfmd only adds
# /opt/kusu/lib/python to PYTHONPATH before spawning cfmclient.
sys.path.append('/opt/primitive/lib/python2.4/site-packages')
sys.path.append('/opt/primitive/lib64/python2.4/site-packages')

from primitive.system.software.probe import OS
from primitive.system.software.dispatcher import Dispatcher
from primitive.support import osfamily

PLUGINS='/opt/kusu/lib/plugins/cfmclient'
CFMFILE='/etc/cfm/.cfmsecret'
YUMCONF='/var/cache/yum/yum.conf'
LOGFILE='/var/log/kusu/cfmclient.log'

# When the cfmclient is updating files on itself it will
# not replace the files in the IGNORELST
IGNORELST = ['/etc/passwd.merge', '/etc/shadow.merge', '/etc/group.merge', '/etc/gshadow.merge']

def log(mesg):
    """log - Output messages to a log file"""
    global DEBUG
    if DEBUG:
        try:
            fp = file(LOGFILE, 'a')
            fp.write('%s %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), mesg))
            fp.close()
        except:
            print "Logging unavailable!"   

class Merger:
    """ The Merger Class is responsible for dealing with merging
    different types of files."""

    def __init__(self):
        pass

    def log(self, mesg):
        log('%s: %s' % (self.__class__.__name__, mesg))

    def mergeFile(self, filename):
        """
        This function is for merging the group, password, and 
        shadow files only.
        """
        if filename in ['/etc/group', '/etc/passwd', '/etc/shadow']:

            # Set up files as path objects
            osfile   = path("/opt/kusu/etc/cfm/%s.OS" % filename)
            t0file   = path("/opt/kusu/etc/cfm/%s.T0" % filename)
            currfile = path(filename)
            apndfile = currfile + '.merge'
            
            # If the saved OS copy does not exist:
            # 1. Make a copy from the current file, keeping same file permissions
            # 2. Remove the entry for 'root' user in the OS copy for shadow
            #    i.e. /opt/kusu/etc/cfm/shadow.OS
            if not osfile.exists():
                if not osfile.dirname().exists():
                    osfile.dirname().makedirs()
                currfile.copy2(osfile)

                if currfile == '/etc/shadow':
                    # Remove the password entry for root from the OS file 
                    self.__removeSelectedLine(osfile, 'root', ':')

            # The t0 file is the state of the file since the last merge
            # operation was executed. The current file is then the state at
            # t+X. Hence, the following finds out what has been added and 
            # removed since the last merge operation.
            added, removed = self.__getLineChanges(currfile, t0file)

            # Remove from OS copy the lines that have been removed since t0
            for line in removed:
                key = line.split(':')[0]
                self.__removeSelectedLine(osfile, key, ':')

            # Add to OS copy the lines that were added since t0
            if added:
                osfile.write_lines(added, append=True)
            
            # Overwrite the current file with contents of the OS file and append file
            self.log("Merging %s and %s into %s\n" % (osfile, apndfile, currfile))
            os.system('cat "%s" "%s" > "%s"' % (osfile, apndfile, currfile))
            apndfile.remove()

            # Update t0 file using copy2 which also preserves permissions
            currfile.copy2(t0file)

        else:
            print "WARNING:  Unhandled file merge for file:  %s.  Ignoring" % currfile 


    def __removeComments(self, lines):
        return [line for line in lines if not line[0] == '#']

    def __getLineChanges(self, origfile, t0file):
        """
        Compare the original and time=0 file for added and removed lines.
        Returns a list of the added and removed lines.
        """
        added = []
        removed = []
        if not t0file.exists():
            return [[], []]

        curr = set(self.__removeComments(origfile.lines()))
        t0   = set(self.__removeComments(t0file.lines()))

        # curr - t0 ==> added since t0
        # t0 - curr ==> removed since t0
        return [curr - t0, t0 - curr]
        

    def __removeSelectedLine(self, infile, key, separator):
        """
        Search through a file removing the line that starts with 
        the given key. Entries in that file are delimited by given
        separator.
        """
        try:
            lines = [line for line in infile.lines() \
                    if not line.split(separator)[0] == key]
                
            infile.write_lines(lines)
        except:
            print "Failed to remove line with key %s from %s" % (key, infile)



class CFMClient:

    def __init__(self, argv):
        self.args        = argv
        self.CFMBaseDir  = ''
        self.osname      = OS()[0].lower()
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
        self.selfupdate  = False  # Flag to indicate that this is on an installer


    def log(self, mesg):
        log('%s: %s' % (self.__class__.__name__, mesg))
    
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
                        self.log("ERROR:  Invalid type argument\n")
                        sys.exit(1)
                else:
                    self.log("ERROR:  Type not specified\n")
                    sys.exit(2)
                    
            elif args[i] == '-i':
                if len(args) > (i+1):
                    self.installers = string.split(args[i+1], ',')
                    i += 1
                else:
                    self.log("ERROR:  Installers not specified\n")
                    sys.exit(3)
            else:
                self.log("ERROR:  Unknown argument\n")
                sys.exit(4)
            i += 1
            
        if self.type == 0 or self.installers == []:
            # User is running this by hand
            self.log("ERROR:  Missing arguments!\n")
            print "ERROR:  Missing arguments.  See the manpage for help."
            sys.exit(5)


    def getProfileVal(self, name):
        """getProfileVal - Returns the value of the NII property from
        /etc/profile.nii with any quotes removed."""
        cmd = "grep %s /etc/profile.nii 2>/dev/null" % name
        val = ''
        proc = os.popen(cmd)
        for line in proc.readlines():
            loc = string.find(line, name)
            if loc < 0:
                continue

            t2 = string.split(line[string.find(line, '=')+1:])[0]
            val = string.strip(t2, '"')
            break
        proc.close()
        return val


    def setupNIIVars(self):
        """setupNIIVars - Read in the needed variables from the profile.nii"""
        self.CFMBaseDir = self.getProfileVal("CFMBaseDir")
        val             = self.getProfileVal("NII_REPO")
        if val:
            self.repoid = os.path.basename(val)
        try:
            self.ngid = string.atoi(self.getProfileVal("NII_NGID"))
        except:
            self.log("ERROR:  Unable to determine NGID.  Got: %s\n" % self.ngid)
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
        filetest = "%s/cfmfiles.lst" % (self.CFMBaseDir)
        self.log("++  Testing for: %s\n" % filetest)
        self.log("++  NGID = %i, CFMBaseDir: %s\n" % (self.ngid, self.CFMBaseDir))
        if os.path.exists(filetest):
            return True

        myIPs = getMyIPs()
        self.log("myIPs = %s, installers = %s\n" % (myIPs, self.installers))
        bestIPlist = bestIP(myIPs, self.installers)
        if len(bestIPlist) == 0:
            # No good one found!
            bestIPlist = self.installers[:]
            
        self.bestinstaller = bestIPlist[random.randint(0, len(bestIPlist)-1)]
        self.log("Using installer: %s from list: %s\n" % (self.bestinstaller, bestIPlist))
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
            gid = grp.getgrnam(grpname)[2]
        except:
            gid = grp.getgrnam('nobody')[2]

        try:
            os.chmod(file, mode)
        except:
            self.log("ERROR:  Failed to set the mode of %s to %s\n" % (file, mode))
            sys.exit(-1)
            
        try:
            os.chown(file, uid, gid)
        except:
            self.log("ERROR:  Failed to set the ownership of %s, UID=%s, GID=%s\n" % (file, uid, gid))



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

        # Make the directory if it does not exist
        if not os.path.exists(os.path.dirname(tmpfile)):
            os.system('mkdir -p %s' % os.path.dirname(tmpfile))
        
        if self.__haveLocalAccess():
            # Copy the file from a directory
            self.log("INFO:  Have local Access\n")
            if cfmfile:
                cfmpath = "%s/%s" % (self.CFMBaseDir, source)
            else:
                cfmpath = "%s/%i/%s" % (self.CFMBaseDir, self.ngid, source)
            if not os.path.exists(cfmpath):
                self.log("ERROR: Unable to locate: %s\n" % cfmpath)
                return -1

            os.system('cp \"%s\" \"%s\" >/dev/null 2>&1' % (cfmpath, tmpfile))

        else:
            # Copy the file from one of the installers.  Make the URL
            if cfmfile:
                url = "http://%s/cfm/%s" % (self.bestinstaller, source)
            else:
                url = "http://%s/cfm/%s/%s" % (self.bestinstaller, self.ngid, source)
            datafile = ''
            try:
                (datafile, header) = urllib.urlretrieve(url, tmpfile)
            except Exception, e:
                import traceback
                msg = str(e)
                tb = traceback.format_exc()
                msg = msg + '\n' + tb + '\n'
                self.log("URL download failed!  Trace: %s" % msg)
                self.log("WARNING: Download from %s Failed!\n" % self.bestinstaller)
                # Download failed.  Try the other IP's
                for ip in self.installers:
                    if cfmfile:
                        url = "http://%s/cfm/%s" % (ip, source)
                    else:
                        url = "http://%s/cfm/%s/%s" % (ip, self.ngid, source)
                    self.log("Trying: %s\n" % url)
                    try:
                        (datafile, header) = urllib.urlretrieve(url, tmpfile)
                        # This one worked.  Switch to it
                        self.bestinstaller = ip[:]
                        break
                    except:
                        pass
                if not datafile:
                    self.log("ERROR:  Failed to download: %s\n" % url)
                    return -1

            # Apache does not return the 404 error code in the header as seen here
            #    Date: Tue, 18 Mar 2008 16:22:11 GMT
            #    Server: Apache/2.2.3 (Red Hat)
            #    Content-Length: 287
            #    Connection: close
            #    Content-Type: text/html; charset=iso-8859-1
            # Instead the data must be parsed for the error, which looks like:
            #    <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
            #    <html><head>
            #    <title>404 Not Found</title>
            #    </head><body>
            #    <h1>Not Found</h1>
            #    <p>The requested URL /repos/1001/booger was not found on this server.</p>
            #    <hr>
            #    <address>Apache/2.2.3 (Red Hat) Server at tyan04 Port 80</address>
            #    </body></html>
            # Put code here to deal with this............................



        # Decrypt and decompress the file (if needed)
        if not cfmfile:
            tmpfile2 = "%s.decrypted.CFMtmpFile" % deststruct[0]
            global CFMFILE
            if os.path.exists(CFMFILE):
                cmd = 'openssl bf -d -a -salt -pass file:%s -in "%s" |gunzip > "%s"' % (CFMFILE, tmpfile, tmpfile2)
            else:
                # *** Really need a better shared secret.  REMOVE THIS LATER
                cmd = 'openssl bf -d -a -salt -pass file:/opt/kusu/etc/db.passwd -in "%s" |gunzip > "%s"' % (tmpfile, tmpfile2)
            proc = os.popen(cmd)
            for line in proc.readlines():
                if line:
                    self.log("ERROR:  %s\n" % line)
                    if os.path.exists(tmpfile2):
                        os.unlink(tmpfile2)
                    if os.path.exists(tmpfile):
                        os.unlink(tmpfile)
                    proc.close()
                    return -1
            proc.close()
            try:
                os.rename(tmpfile2, tmpfile)
            except OSError, e:
                self.log("ERROR: unable to rename %s to %s: %s" % (tmpfile2, tmpfile, e))
                return -1

        # Set the file permissions
        self.__setFilePerms(tmpfile, deststruct[1], deststruct[2], deststruct[3])

        # If an md5sum is provided test the file.
        try:
            origmd5sum = deststruct[4]
            cmd = '%s "%s"' % (self.md5sum, tmpfile)
            md5sum = '-none-'
            proc = os.popen(cmd)
            for line in proc.readlines():
                bits = string.split(line)
                md5sum = bits[0]
                if origmd5sum != md5sum:
                    self.log("ERROR:  The checksum of the received file, and the original do not match.  Aborting transfer!\n")
                    self.log("Filename = %s\n" % tmpfile)
                    self.log("origmd5sum= %s   md5sum= %s\n" % (origmd5sum, md5sum))
                    os.unlink(tmpfile)
                    proc.close()
                    return -1
            proc.close()

        except:
            # No md5sum provided
            pass
        
        os.rename(tmpfile, deststruct[0])
        return 0


    def __setupForYum(self):
        """__setupForYum  - Make a yum.conf pointing to the installer that is closest"""
        dirname = Dispatcher.get('yum_repo_subdir', 'Server')

        global YUMCONF
        yumconf = YUMCONF
        fp = file(yumconf, 'w')
        out = ( '[main]\n'
                'cachedir=/var/cache/yum\n'
                'debuglevel=2\n'
                'logfile=/var/log/yum.log\n'
                'reposdir=/dev/null\n'
                'retries=20\n'
                'timeout=30\n'
                'assumeyes=1\n'
                'gpmcheck=0\n'
                'tolerant=1\n\n'
                '[kusu-installer]\n'
                'name=%s - Booger\n'
                'baseurl=http://%s/repos/%s%s\n' % (self.osname, self.bestinstaller, self.repoid, dirname)
                )

        fp.write(out)
        fp.close()
        
    def __runCommand(self, cmd):
        self.log("Running:  %s\n" % cmd)
        proc = os.popen(cmd)
        for line in proc.readlines():
            self.log(line)
        proc.close()

    def __runCommand2(self, cmd):
        self.log("Running:  %s\n" % cmd)
        p = subprocess.Popen(cmd, shell=True, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
        (sout, serr) = p.communicate()
        try:
            p.wait()
        except:
            pass
        try:
            p.stdin.close()
            p.stdout.close()
        except:
            pass

    def __setupZypperSource(self):
        """
        Backup existing sources and caches and create just one source that points
        to the closest installer.
        """
        atexit.register(self.__restoreZypperSources)

        sources_dir = path(Dispatcher.get('zypper_sources_dir'))
        cache_dir = path(Dispatcher.get('zypper_cache_dir'))

        if sources_dir.exists():
            self.temp_dir = path(tempfile.mkdtemp(prefix=self.__class__.__name__, 
                                                  dir=Dispatcher.get('zypper_base_dir', default='/tmp')))
            (self.temp_dir / 'sources').mkdir()
            (self.temp_dir / 'cache').mkdir()

            # Move all source files to the temp_dir
            cmd = "mv %s/* %s/sources" % (sources_dir, self.temp_dir)
            self.__runCommand(cmd)

            # Move all directories in the cache_dir to the temp_dir
            cmd = "mv %s/* %s/cache" % (cache_dir, self.temp_dir)
            self.__runCommand(cmd)

            # Add the installer as the only source
            cmd = "echo y | /usr/bin/zypper service-add http://%s/repos/%s %s >> %s 2>&1" % (self.bestinstaller, self.repoid, self.osname, LOGFILE)
            self.__runCommand2(cmd)
        
    def __restoreZypperSources(self):
        """
        Restore the sources that were backed up earlier in __setupZypperSource.
        """
        sources_dir = path(Dispatcher.get('zypper_sources_dir'))
        cache_dir = path(Dispatcher.get('zypper_cache_dir'))

        if sources_dir.exists() and \
                cache_dir.exists() and \
                hasattr(self, 'temp_dir') and \
                (self.temp_dir / 'sources').exists() and \
                (self.temp_dir / 'cache').exists():

            # Remove the installer source added earlier
            cmd = "echo y | /usr/bin/zypper service-delete http://%s/repos/%s >> %s 2>&1" % (self.bestinstaller, self.repoid, LOGFILE)
            self.__runCommand2(cmd)

            # Move the original zypper sources back
            cmd = "mv %s/sources/* %s" % (self.temp_dir, sources_dir)
            self.__runCommand(cmd)

            # Delete cache directories
            for dir in cache_dir.dirs():
                dir.rmtree()

            # Move the original zypper caches back
            cmd = "mv %s/cache/* %s" % (self.temp_dir, cache_dir)
            self.__runCommand(cmd)

            self.temp_dir.rmtree()

    def __installPackages(self):
        """__installPackages - Install the packages in the list."""

        if not self.newpackages:
            self.log("Nothing to add\n")
            return
        
        cmd = ''
        if self.osname in osfamily.getOSNames('rhelfamily') + ['fedora']:
            global YUMCONF
            self.__setupForYum()

            cmd = "/usr/bin/yum -y -c %s clean all >> %s 2>&1" % (YUMCONF, LOGFILE)
            self.__runCommand2(cmd)
            
            cmd = "/usr/bin/yum -y -c %s install " % YUMCONF

        elif self.osname in ['sles', 'opensuse', 'suse']:
            self.__setupZypperSource()
            cmd = "echo y | %s" % Dispatcher.get('zypper_install_cmd')
    
        if cmd:
            for i in self.newpackages:
                # Using redirection here because the p.communicate deadlocks
                cmd2 = "%s %s >> %s 2>&1" % (cmd, i, LOGFILE)
                self.__runCommand2(cmd2)

    def __removePackages(self):
        """__removePackages - Remove the packages in the list."""
        if not self.oldpackages:
            self.log("Nothing to remove\n")
            return
       
        cmd = ''
        if self.osname in ['rhel', 'fedora', 'centos']:
            global YUMCONF
            self.__setupForYum()
            cmd = "/usr/bin/yum -y -c %s remove" % YUMCONF

        elif self.osname in ['sles', 'opensuse', 'suse']:
            self.__setupZypperSource()
            cmd = "echo y | %s" % Dispatcher.get('zypper_remove_cmd')

        if cmd:
            for i in self.oldpackages:
                # Using redirection here because the p.communicate deadlocks
                cmd2 = "%s %s >> %s 2>&1" % (cmd, i, LOGFILE)
                self.__runCommand2(cmd2)
                

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

        # Strip out duplicates
        oldlist.sort()
        tmplst = oldlist[:]
        for i in xrange(1, len(tmplst)):
            if tmplst[i-1] == tmplst[i]:
                oldlist.remove(tmplst[i])

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
            self.log("Found new package: %s\n" % entry)

        # Anything still in oldlist is a package to remove
        self.oldpackages = []
        for entry in oldlist:
            # Skip yum and rpm
            if entry == 'yum' or entry == 'rpm':
                self.log("WARNING:  Can't remove: %s\n" % entry)
                continue
            if entry:
                self.oldpackages.append(entry)
            self.log("Found old package: %s\n" % entry)


    def __processFileName(self, filename):
        """__processFileName - The filename from the cfmfile list contains
        additional information on how the file should be treated.  This
        function returns a tuple with:  "filename.action", "action"
        The action will be ignored if it is from another node group."""

        # Determine is any special processing is needed
        action = ''
        if filename[-7:] == '.append':
            action = 'append'
        if filename[-6:] == '.merge':
            action = 'merge'

        fn = filename
        #if action:
        #    fn = filename[:-(len(action) + 1)]
        #else:
        #    fn = filename

        # Test to see if this is in the same node group
        try:
            ng = string.atoi(string.split(fn[(len(self.CFMBaseDir)):], '/')[1])
            if ng != self.ngid:
                action = 'ignore'
        except ValueError:
            self.log('Path does not match expected format. This may be due to wrong or unset CFMBaseDir')
            action = 'ignore'

        # Now strip off the leading CFMBaseDir, and NGID
        fn = fn[(len(self.CFMBaseDir) + len("%i" % self.ngid) + 1):]
        
        if self.selfupdate and action != 'ignore':
            # Set this to ignore if this is the installer and it is one
            # of the files not to replace
            if fn in IGNORELST:
                action = 'ignore'
                self.log("Not replacing: %s\n" % fn)

        return (fn, action)


    def __findOlderFiles(self, force=0):
        """__findOlderFiles  - This function will read the cfmfiles.lst, and
        locate files in that list that are older than the timestamp in the
        file, then populate the self.newfiles with the list of files to
        update.  If the force option is provided and is non-zero then all
        files will be updated.  This is to deal with newly installed nodes
        where the timestamp on the files is always newer then the CFM file."""
        try:
            filep = open(self.cfmfilelst, 'r')

        except:
            self.log("ERROR:  Could not open: %s\n" % self.cfmfilelst)
            return
        
        for line in filep.readlines():
            if line[0] == '#':
                continue
            if line:
                # e.g.  /opt/kusu/cfm/5/opt/kusu/etc/package.lst apache apache
                #              420 1181168668 8c1a2bb5be7c8a4c8279484772fccf01
                chunks = string.split(line)
                md5sum = chunks[-1:][0]
                time   = string.atoi(chunks[-2:-1][0])
                tmode  = chunks[-3:-2][0]
                group  = chunks[-4:-3][0]
                user   = chunks[-5:-4][0]
                filen  = string.join(chunks[:-5], ' ')
                filename, action = self.__processFileName(filen)

                if action == 'ignore':
                    continue

                # Make mode an octal number
                mode = string.atoi(tmode, 8)
                    
                # Only look at destination file
                fn = filename
                if action != '':
                    fn = filename[:-(len(action) + 1)]

                # Force the file installation
                if force != 0:
                    self.newfiles.append([filename, user, group, mode, action, md5sum])
                    continue
                
                # Test to see if it's newer
                if os.path.exists(fn):
                    mtime = os.path.getmtime(fn)
                    if mtime < time:
                        self.log(" ++ Going to get: %s\n" % filename)
                        self.log("local file time=%i, remote file time=%i\n" % (mtime, time))
                        # File needs to be updated
                        self.newfiles.append([filename, user, group, mode, action, md5sum])
                    elif action == '':
                        # Test the md5sum of the file to see if it differs
                        # NOTE:  This is only valid if the action is ''
                        cmd = '%s "%s"' % (self.md5sum, filename)
                        origsum = '-none-'
                        proc = os.popen(cmd)
                        for line in proc.readlines():
                            bits = string.split(line)
                            origsum = bits[0]
                            if origsum != md5sum:
                                self.log(" ++ Md5sum differs Going to get: %s\n" % filename)
                                self.newfiles.append([filename, user, group, mode, action, md5sum])
                        proc.close()
                    else:
                        # Special case.  For merging files we cannot use the md5sum.  Have to merge anyway
                        self.log(" ++ Local file is newer!  Action=%s  Going to get: %s\n" % (action, filename))
                        self.newfiles.append([filename, user, group, mode, action, md5sum])
                else:
                    self.log("NOTICE:  File: %s does not exist!\n" % filename)
                    self.newfiles.append([filename, user, group, mode, action, md5sum])

        filep.close()
                                         

    def __installNewFiles(self):
        """__installNewFiles - Install the files in the  self.newfiles list"""
        for filename, user, group, mode, action, md5sum in self.newfiles:

            attr = (filename, user, group, mode, md5sum)
            self.log("Updating file: %s\n" % filename)
            retval = self.__getFile(filename, attr, 0)
            if retval:
                continue
            
            # Determine what to do based on the action
            if action == '':
                continue
            elif action == 'append':
                realfile = filename[:-(len(action) + 1)]
                osfile   = "/opt/kusu/etc/%s.OS" % realfile
                if not os.path.exists(osfile):
                    self.log("Copying original file to: %s\n" % osfile)
                    os.system('mkdir -p \"%s\"' % os.path.dirname(osfile))
                    if os.path.exists(realfile):
                        os.system('cp \"%s\" \"%s\"' % (realfile, osfile))
                    else:
                        fin = open(osfile, 'w')
                        fin.close()

                self.log("Combining: %s and %s to %s\n" % (osfile, filename, realfile))
                os.system('cat \"%s\" \"%s\" > \"%s\"' % (osfile, filename, realfile))
                os.unlink(filename)
            elif action == 'merge':
                # This is for the group passwd, and shadow files.
                realfile = filename[:-(len(action) + 1)]
                merger = Merger()
                merger.mergeFile(realfile)
            else:
                self.log("WARNING: Unknown action type: %s for %s\n" % (filename, action) )


    def __runPlugins(self):
        """__runPlugins - Run any plugins found in the PLUGINS directory.
        These can be any type of executable.  The list of plugins will be
        sorted then run. """
        global PLUGINS
        sys.path.append(PLUGINS)
        
        flist = glob.glob('%s/*' % PLUGINS)
        if len(flist) == 0:
            return

        flist.sort()

        for plugin in flist:
            if plugin[-7:] == '.remove':
                continue
            self.log("Running plugin: %s\n" % plugin)
            os.system('/bin/sh %s >/dev/null 2>&1' % plugin)


    def __removeDeps(self):
        """__removeDeps - Run any plugin found in the PLUGINS directory that
        end in .remove   These can be any type of executable.  The list of
        plugins will be sorted then run. """
        global PLUGINS
        sys.path.append(PLUGINS)
        
        flist = glob.glob('%s/*.remove' % PLUGINS)
        if len(flist) == 0:
            return

        flist.sort()

        for plugin in flist:
            self.log("Running plugin: %s\n" % plugin)
            os.system('/bin/sh %s' % plugin)
            if os.path.exists(plugin):
                try:
                    os.unlink(plugin)
                except:
                    pass


    def updatePackages (self):
        """updatepackages - Update packages"""
        self.log("Updating Packages\n")
        if os.path.exists(self.packagelst):
            os.rename(self.packagelst, '%s.ORIG' % self.packagelst)
        attr = (self.packagelst, 'root', 'root', 0600)
        if self.__getFile('%i.%s' % (self.ngid, self.pkglstpost), attr, 1):
            # Download failed
            self.log("Failed to download package list.  Aborting!\n")
            if os.path.exists('%s.ORIG' % self.packagelst):
                os.rename('%s.ORIG' % self.packagelst, self.packagelst)
                return -1

        # Test the package file to see if it is valid
        testdata = self.__getFileEntries(self.packagelst)
        if len(testdata) != 0 and testdata[0][0] == '<':
            # This is not proper content
            self.log("ERROR:  Failed to get the package.lst.\n")
            if os.path.exists('%s.ORIG' % self.packagelst):
                os.rename('%s.ORIG' % self.packagelst, self.packagelst)
        else:
            self.__getPackageChanges()
            try:
                self.__removePackages()
                self.__removeDeps()
                self.__installPackages()
                self.__runPlugins()
                if os.path.exists('%s.ORIG' % self.packagelst):
                    os.unlink('%s.ORIG' % self.packagelst)
            except:
                # Revert old package list so we can retry
                if os.path.exists('%s.ORIG' % self.packagelst):
                    os.rename('%s.ORIG' % self.packagelst, self.packagelst)

        # Mark the node as Installed instead of Expired
        datafile = ''
        url = "http://%s/repos/nodeboot.cgi?state=Installed" % self.bestinstaller
        try:
            (datafile, header) = urllib.urlretrieve(url)
        except:
            pass


    def updateFiles (self, force):
        """updatefiles - Update files"""
        self.log("Updating Files\n")
        # Update the package list.
        attr = (self.cfmfilelst, 'root', 'root', 0600)
        self.__getFile('cfmfiles.lst', attr, 1)
        self.__findOlderFiles(force)
        self.__installNewFiles()
        if len(self.newfiles):
            self.__runPlugins()


    def updateRepo (self):
        """updateRepo - Update all new install files in repo"""
        self.log("Updating To New Repo Packages\n")

        self.__haveLocalAccess()

        # Just running:  yum update
        if self.osname in ['rhel', 'fedora', 'centos']:
            global YUMCONF
            self.__setupForYum()

            cmd = "/usr/bin/yum -y -c %s clean metadata >> %s 2>&1" % (YUMCONF, LOGFILE)
            self.__runCommand2(cmd)

            cmd = "/usr/bin/yum -y -c %s clean all >> %s 2>&1" % (YUMCONF, LOGFILE)
            self.__runCommand2(cmd)
            
            cmd = "/usr/bin/yum -y -c %s update >> %s 2>&1" % (YUMCONF, LOGFILE)
            self.__runCommand2(cmd)

        elif self.osname in ['sles', 'opensuse', 'suse']:
            self.__setupZypperSource()
            cmd = "echo y | %s >> %s 2>&1" % (Dispatcher.get('zypper_update_cmd'), LOGFILE)
            self.__runCommand2(cmd)

    def run (self):
        """run - Entry point for CFM client"""
        self.parseargs()
        
        # Check if root user
        if os.geteuid():
            print "ERROR:  Only root can run this tool\n"
            sys.exit(-1)
            
        if self.installers[0] != 'self':
            self.setupNIIVars()
        else:
            self.selfupdate = True
            # This is the installer to try the database
            self.ngid = 1
            #try:
            #    from kusu.core.db import KusuDB
            #except:
            #    print "Database modules are unavailable!"
            #    sys.exit(-1)
#
#            db = KusuDB()
#            db.connect('kusudb', 'apache')
#            query = ('select repos.repoid, repos.ostype from repos, nodegroups where nodegroups.ngid=1 and nodegroups.repoid=repos.repoid')
#            try:
#                db.execute(query)
#                data = db.fetchone()
#            except:
#                print "Failed to connect to database!"
#                sys.exit(-1)
#                
#            self.repoid = data[0]
#            self.ostype = data[1]
#            self.CFMBaseDir = db.getAppglobals('CFMBaseDir')

            # XXX: Workaround until we have a profile.nii on installer
            self.repoid = 1000

            # Exit if os is not supported
            if not (self.osname in ['rhel', 'centos', 'fedora', 'scientificlinux', 'sles', 'opensuse', 'suse']):
                sys.exit(-1)

            self.CFMBaseDir = '/opt/kusu/cfm'
            self.bestinstaller = '127.0.0.1'
            
        global UPDATEFILE
        global UPDATEPACKAGE
        global FORCEFILES
        global UPDATEREPO
        if not self.installers or not self.type:
            print "Usage:  {cmd} -t [TYPE] -i {Installer list}"
            sys.exit(-1)

        force = 0
        if self.type & FORCEFILES:
            self.log("INFO:  Forcing update of all files.\n")
            force = 1
            
        if self.type & UPDATEFILE:
            self.updateFiles(force)

        if self.type & UPDATEPACKAGE:
            self.updatePackages()

        if self.type & UPDATEREPO:
            self.updateRepo()

        sys.exit(0)



if __name__ == '__main__':
    app = CFMClient(sys.argv)
    app.run()
