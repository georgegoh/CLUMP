#!/usr/bin/python
#
# $Id$
#
#  Copyright (C) 2007 Platform Computing
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

from optparse import OptionParser
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB

CFMFILE = '/etc/cfm/.cfmsecret'

class BuildInitrd:
    """This class will provide the initrd management functions"""

    def __init__(self):
        """__init__ - initializer for the class"""
        self.db          = KusuDB()
        self.database    = 'kusudb'
        self.user        = 'apache'
        self.password    = ''
        self.nodegroup   = ''     # Node group name
        self.ngid        = 0      # Node group database ID
        self.repoid      = 0      # Repository ID from database
        self.repodir     = ''     # The location of the repository to use
        self.installtype = ''     # The type of the installation
        self.modules     = []     # A list of all the modules to include
        self.ostype      = ''     # The ostype for the repository
        self.kernel      = ''     # The name of the kernel to use from db
        self.initrd      = ''     # The name of the initrd
        self.initrd64    = '/opt/kusu/initrds/rootfs.x86_64.cpio.gz'   # 64bit image
        self.initrd32    = '/opt/kusu/initrds/rootfs.i686.cpio.gz'     # 32bit image
        self.gettext     = 0
        self.imagedir    = ''     # Location of the initial ram disk image
        self.moduledir   = ''     # Location of the temporary module directory
        self.modlink     = ''     # Symbolic link to self.moduledir  (fix for depmod.pl bug)
        self.initlink    = ''     # Symbolic link to self.imagedir   (fix for depmod.pl bug)
        self.db.connect(self.database, self.user)
        self.stderrout   = 0      # Method for outputting to STDERR with internationalization
        self.stdoutout   = 0      # Method for outputting to STDOUT with internationalization

        
    def altDb(self, database, user, password):
        """altDb - Change the database user, password and database"""
        self.database = database
        self.user     = user
        self.password = password
        self.db.disconnect()
        self.db.connect(self.database, self.user, self.password)

        
    def setTextMeths(self, stderrmeth, stdoutmeth):
        """setTextMeths - Initialize the function pointers to allow output to STDERR
        and STDOUT with internationalization."""
        self.stderrout = stderrmeth
        self.stdoutout = stdoutmeth

        
    def makeInitrd(self, nodegroup, image, type):
        """makeImage - This method will create a image for a given node group.
        It will optionally name the image."""

        if not self.validateNG(nodegroup):
            if self.stderrout:
                self.stderrout("ERROR: Invalid node group: %s\n", nodegroup)
            return

        # Get a list of modules to add
        self.getModules()
        if len(self.modules) == 0:
            if self.stderrout:
                self.stderrout("No modules to add!\n")
            return
        
        # Get the repository information
        self.getRepoInfo()

        # Make a directory with the template initrd in it
        self.mkInitrdDir()

        # Extract the modules from the OS kernel package
        self.extractModules(oskernel=1)

        # Patch in the modules that are from the OS
        self.addModules()

        # Copy over the kernel (Required because of signed modules)
        self.addKernel()
        
        # Extract and add any vendor modules if found
        if self.extractModules(oskernel=0):
            self.addModules()
        
        # Compact the initrd and move it to the tftp directory
        self.compactInitrd(type)

        # Clean-up directory for next run
        os.system('rm -rf \"%s\"' % self.modlink)
        os.system('rm -rf \"%s\"' % self.initlink)
        os.system('rm -rf \"%s\"' % self.moduledir)
        os.system('rm -rf \"%s\"' % self.imagedir)
        

    def validateNG(self, nodegroup):
        """validateNG - Test the node group name to make sure it is valid.
        Returns:  True - when the node group exists, otherwise False.
        It will also set the self.ngid to the value from the database."""
        query = ('select ngid, repoid, installtype, kernel, initrd from nodegroups '
                 'where ngname="%s"' % nodegroup )
        try:
            self.db.execute(query)
            data = self.db.fetchone()
        except:
            return False
        if data:
            self.ngid, self.repoid, self.installtype, self.kernel, self.initrd = data
            self.nodegroup = nodegroup
            if not self.initrd:
                self.makeInitrdName()
            return True
        return False


    def makeInitrdName(self):
        """makeInitrdName - generate a name for the initrd."""
        initrd = "initrd.%s.%s.img" % (self.installtype, self.ngid)
        query = ('update nodegroups set initrd="%s" where ngid="%s"'
                 % (initrd, self.ngid) )
        try:
            self.db.execute(query)
            data = self.db.fetchone()
            self.initrd = initrd
        except:
            return False
        

    def mkInitrdDir(self):
        """mkInitrdDir - Make a directory to store the initrd in and expand
        the template initrd into that directory."""

        idir = self.db.getAppglobals('ImageBaseDir')
        if not idir:
            idir = '/depot/images'

        # Get the architecture from the kits that are part of the repo
        query = ('select kits.arch from kits,repos_have_kits,repos,nodegroups '
                 'where nodegroups.repoid=repos.repoid and '
                 'repos.repoid=repos_have_kits.repoid and '
                 'repos_have_kits.kid=kits.kid and kits.arch is not NULL ' 
                 'and nodegroups.ngid="%s"' % self.ngid)
        try:
            self.db.execute(query)
            data = self.db.fetchone()
        except:
            if self.stderrout:
                self.stderrout("DB_Query_Error: %s\n", query)

            sys.exit(-1)

        arch = 'x86'

        if data:
            arch = data[0]

        if arch == 'x86_64':
            template = self.initrd64
        else:
            template = self.initrd32

        self.imagedir  = os.path.join(idir, '%s-initrd' % self.nodegroup)
        self.moduledir = os.path.join(idir, '%s-modules' % self.nodegroup)
        self.modlink   = os.path.join(idir, 'modules')
        self.initlink  = os.path.join(idir, 'initrd')
        
        if not os.path.exists(idir):
            os.system('mkdir -p %s' % idir)
            
        if os.path.exists(self.imagedir):
            if self.stdoutout:
                self.stdoutout("Removing: %s\n", self.imagedir)
            os.system('rm -rf \"%s\"' % self.imagedir)
            
        os.mkdir(self.imagedir, 0700)
        
        if os.path.exists(self.moduledir):
            if self.stdoutout:
                self.stdoutout("Removing: %s\n", self.moduledir)
            os.system('rm -rf \"%s\"' % self.moduledir)
        os.mkdir(self.moduledir, 0700)

        # Make symbolic links to the directories, because depmod.pl can't
        # have spaces in the path.
        if os.path.lexists(self.modlink):
            os.unlink(self.modlink)

        if os.path.lexists(self.initlink):
            os.unlink(self.initlink)

        os.system('ln -s \"%s\" %s' % (self.moduledir, self.modlink))
        os.system('ln -s \"%s\" %s' % (self.imagedir, self.initlink))

        # Extract the template
        os.chdir(self.imagedir)
        if self.stdoutout:
                self.stdoutout("Extracting template Initial Ram Disk\n")
                print "%s" % template
        os.system('zcat %s |cpio -id >/dev/null' % template) 

        # Add the CFM data
        global CFMFILE
        if os.path.exists(CFMFILE):
            os.system('cp %s \"%s\"' % (CFMFILE,  self.imagedir))


    def getModules(self):
        """getModules - Returns a list of modules that this
        image should contain."""

        # Get the list of all the optional packages to add.
        self.modules = []
        query = ('select distinct module from modules where ngid="%s" '
                 'order by loadorder' % self.ngid )
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            if self.stderrout:
                self.stderrout("DB_Query_Error: %s\n", query)
                
            sys.exit(-1)

        if data:
            for row in data:
                self.modules.append(row[0])


    def extractModules(self, oskernel=1):
        """extractModules - Extract the kernel package into a tempory
        directory, so that the modules can be extracted."""

        if oskernel:
            # First look for the OS kit kernel RPM package.
            query = ('select dpname from '
                     'nodegroups, repos_have_kits, kits, components, driverpacks '
                     'where nodegroups.repoid=repos_have_kits.repoid and '
                     'repos_have_kits.kid=components.kid and '
                     'kits.isOS="1" and driverpacks.cid=components.cid and '
                     'nodegroups.ngid="%s"' % self.ngid)

        else:
            # Look for vendor kernel modules.
            query = ('select dpname from ng_has_comp, components, driverpacks, kits '
                     'where ng_has_comp.cid=components.cid and '
                     'components.kid=kits.kid and kits.isOS<>"1" and '
                     'driverpacks.cid=components.cid and '
                     'ng_has_comp.ngid="%s"' % self.ngid)

        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            if self.stderrout:
                self.stderrout("DB_Query_Error: %s\n", query)
                sys.exit(-1)

        if not data:
            if oskernel:
                if self.stderrout:
                    self.stderrout("ERROR: Kitops has failed to update the driverpacks table!  Fix this!\n")
                    self.stderrout("DB_Query_Error: %s\n", query)
                    sys.exit(-1)
            return 0

        for row in data:
            # There can be more than one package.  All have to be processed
            if self.stdoutout:
                self.stdoutout("Looking for modules in: %s\n", row[0])
                
            # Warning OS Specific Stuff
            pattern = '/nonexistant/stuff'
            if self.ostype[:6] == 'fedora':
                pattern = '%s/Fedora/RPMS/%s' % (self.repodir, row[0])
            elif self.ostype[:4] == 'rhel':
                pattern = '%s/*/%s' % (self.repodir, row[0])
            elif self.ostype[:6] == 'centos':
                pattern = '%s/*/%s' % (self.repodir, row[0])
                
            flist = glob.glob(pattern)

            if len(flist) == 0:
                if self.stderrout:
                    # Fatal error
                    self.stderrout("ERROR: Unable to locate kernel package in: %s  Try running:  ls %s\n"
                                   % (self.repodir, pattern) )
                    sys.exit(-1)

            # If there is more than one package available use the highest rev
            if len(flist) > 1:
                # Use the last.  Seems to be the highest rev
                kpkg = "%s" % flist[-1]
            else:
                kpkg = "%s" % flist[0]

            # Extract the package.  This is OS specific
            if self.stdoutout:
                self.stdoutout("Extracting modules\n")

            if kpkg.split('.')[-1] == 'rpm':
                os.system('mkdir -p \'%s\'' % self.moduledir)
                os.chdir(self.moduledir)
                os.system('rpm2cpio %s |cpio -id >/dev/null 2>&1' % kpkg)

            elif kpkg.split('.')[-1] == 'deb':
                os.system('mkdir -p \'%s\'' % self.moduledir)
                os.chdir(self.moduledir)
                os.system('deb2cpio %s |cpio -id >/dev/null' % kpkg)  # Fix this
            else:
                print "kpkg = %s" % kpkg
                print "len(flist) = %i" % len(flist)
                if self.stderrout:
                    # Fatal error
                    self.stderrout("ERROR: Unknown kernel package type: %s" % kpkg )
                    sys.exit(-1)

        return 1

        
    def getRepoInfo(self):
        """getRepoInfo - Gather the info for the repo we are going to use.
        """
        query = ('select repository, ostype from repos,nodegroups where '
                 'repos.repoid=nodegroups.repoid and ngid="%s"' % self.ngid)
        try:
            self.db.execute(query)
            data = self.db.fetchone()
        except:
            if self.stderrout:
                self.stderrout("DB_Query_Error: %s\n", query)

            sys.exit(-1)

        if data:
            self.repodir, self.ostype = data


    def addKernel(self):
        """addKernel - The kernel modules are signed.  This means that the
        kernel and modules MUST match.  We then have to take the kernel from
        the OS package and use that, otherwise the modules will not load."""
        if self.stdoutout:
            self.stdoutout("Copying over kernel\n")
        else:
            print "Copying over kernel"

        pattern = '%s/boot/vmlinuz*' % self.moduledir
        flist = glob.glob(pattern)

        if len(flist) == 0:
            if self.stderrout:
                # Fatal error
                self.stderrout("ERROR: Unable to locate kernel!  Try running:  ls %s\n"
                               % (pattern) )
                sys.exit(-1)

        # If there is more than one package available use the highest rev
        if len(flist) > 1:
            # Use the last.  Seems to be the highest rev
            kern = "%s" % flist[-1]
        else:
            kern = "%s" % flist[0]

        # Fedora has kernel packages with the exact same name.  We have
        # to use our own naming convention.
        kernname = 'kernel.%s.%s' % (self.installtype, self.ngid)
        if kernname != self.kernel:
            # Update database
            query = ('update nodegroups set kernel="%s" where ngid="%s"' % (kernname,self.ngid))
            try:
                self.db.execute(query)
                data = self.db.fetchone()
            except:       
                if self.stderrout:
                    self.stderrout("DB_Query_Error: %s\n", query)
                    sys.exit(-1)

        os.system('cp \"%s\" \"/tftpboot/kusu/%s\"' % (kern, kernname)) 
        

    def addModules(self):
        """addModules - This method will locate the kernel package and extract
        the needed modules from it.  These will be copied to the initrd.  It
        will call depmod to build the needed kernel files."""

        if self.stdoutout:
            self.stdoutout("Patching in modules:\n")
        else:
            print "Patching in modules:"

        mlist = self.modules[:]
        for root, dirs, files in os.walk(self.moduledir):
            if files and mlist:
                # print root
                for file in files:
                    # Remove the '.ko' extension
                    t = '%s' % file
                    mname = t.split('.')[0]
                    for mod in mlist:
                        if mod == mname:
                            print "%s " % (mod),
                            mlist.remove(mod)
                            newloc = "%s/%s" % (self.imagedir, root[len(self.moduledir):])
                            oldloc = "%s/%s" % (root, file)
                            if not os.path.exists(newloc):
                                os.system('mkdir -p \"%s\"' % newloc)
                                # print 'Running: mkdir -p \"%s\"' % newloc
                            os.system('cp \"%s\" \"%s\"' % (oldloc, newloc))
                            #print 'Running: cp \"%s\" \"%s\"' % (oldloc, newloc)
        print " "
        if mlist:
            if self.stderrout:
                list = ''
                for mod in mlist:
                    list = list + "%s\t" % (mod)
                    
                self.stderrout("INFO: Did not locate module(s): %s\n", list)

        # Add a load order list
        fp = open('%s/etc/module-load-order.lst' % self.imagedir, 'w')
        for m in self.modules:
            out = "%s\n" % m
            fp.write(out)
        fp.close()

        # Add the libraries for the imageinit
        pattern = '%s/usr/lib/python2*' % self.imagedir

        flist = glob.glob(pattern)
        if len(flist) == 0:
            if self.stderrout:
                # Fatal error
                self.stderrout("ERROR: Unable to locate python package in: %s  Try running:  ls %s\n"
                               % (self.imagedir, pattern) )
                sys.exit(-1)
        pythondir = "%s" % flist[0]
        os.system('cp -r /opt/kusu/lib/python/kusu/* \"%s\"' % pythondir)
        os.system('cp /opt/kusu/etc/imageinit.py \"%s\"' % self.imagedir)
        file = '%s/imageinit.py' % self.imagedir
        # print 'Running:  cp /opt/kusu/etc/imageinit.py %s' % file
        os.chmod(file, 0755)

        # Add the entry to startup imageinit.py at boot (Too lazy to open write close)
        os.chdir(self.imagedir)
        # os.system('echo "null::sysinit:/imageinit.py" >> etc/inittab')
        os.system('rm -rf init')
        os.system('cp /opt/kusu/etc/imageinit.sh init')
        os.system('chmod 755 init')


        # Add the entry to switch the root filesystem
        # os.system('echo "null::sysinit:/sbin/switch_root /newroot /sbin/init" >> etc/inittab')

        # Change the /etc/issue
        os.system('echo "Kusu Initial Ram Disk" > etc/issue')
        
        # Locate the System map, then run depmod
        os.chdir(self.imagedir)
        pattern  = ''
        pattern2 = ''
        if self.ostype[:6] == 'fedora' or self.ostype[:4] == 'rhel' or self.ostype[:6] == 'centos':
            pattern  = os.path.join(self.modlink, 'boot/System.map*')
            pattern2 = os.path.join(self.initlink, 'lib/modules/2*')
            
        if pattern:
            flist  = glob.glob(pattern)
            flist2 = glob.glob(pattern2)
            if len(flist) > 0 and len(flist2) > 0:
                os.system('/opt/kusu/etc/depmod.pl -b %s -F %s' % (flist2[0], flist[0]))
                return

            if len(flist2) > 0:
                if self.stderrout:
                    self.stderrout("WARNING: Unable to use System.map to verify module symbols\n")

                os.system('/opt/kusu/etc/depmod.pl -b %s -k /tftpboot/kusu/%s' % (flist2[0], self.kernel))
                
        else:
            print "Unsupported OS!  Fix me!"



    def compactInitrd(self, type):
        """compactInitrd - This method will generate the final initrd image.
        in initrd, or initramfs format (depending on type), and copy it to the
        TFTP server directory."""
        if self.stdoutout:
            self.stdoutout("Packing initial RAM Disk\n")
        else:
            print "Packing initial RAM Disk"

        if type == 'initrd':
            print "FIX ME"

        else:
            os.chdir(self.imagedir)
            os.system('find . | cpio --quiet -o -H newc | gzip > \"/tftpboot/kusu/%s\"' % 
                      self.initrd)
            print "Wrote:  /tftpboot/kusu/%s" %  self.initrd


class BuildInitrdApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)


    def toolVersion(self):
        """toolVersion - provide a version screen for this tool."""
        global version
        self.stdoutMessage("Version %s\n", self.version)
        sys.exit(0)


    def toolHelp(self):
        """toolHelp - provide a help screen for this tool."""
        self.stdoutMessage("buildinitrd_Help")
        sys.stdout.write('\n')
        sys.exit(0)


    def parseargs(self):
        """parseargs - Parse the command line arguments and populate the
        class variables"""
        
        self.parser.add_option("-n", "--nodegroup", action="store",
                               type="string", dest="nodegrp")
        self.parser.add_option("-i", "--image", action="store",
                               type="string", dest="image")
        self.parser.add_option("-d", "--database", action="store",
                               type="string", dest="database")
        self.parser.add_option("-u", "--user", action="store",
                               type="string", dest="user")
        self.parser.add_option("-p", "--password", action="store",
                               type="string", dest="password")
        self.parser.add_option("-t", "--type", action="store",
                               type="string", dest="type")
        self.parser.add_option("-v", "--version", action="store_true",
                               dest="wantver", default=False)

        (self.options, self.args) = self.parser.parse_args(sys.argv)

            

    def run(self):
        """run - Run the application"""
        self.parseargs()
        image = ''

        imgfun = BuildInitrd()
        imgfun.setTextMeths(self.errorMessage, self.stdoutMessage)
        
        if self.options.wantver:
            # Print version
            self.toolVersion()
            sys.exit(0)

        # Do we need a new database connection?
        if self.options.database or self.options.user or self.options.password :
            if self.options.database == '' or self.options.user == '' or self.options.password == '':
                self.errorMessage("genconfig_provide_database_user_password\n")
                sys.exit(-1)
                
            imgfun.altDb(self.options.database, self.options.user, self.options.password)
            
        if self.options.image:
            image = self.options.image

        type = 'initramfs'
        if self.options.type:
            if self.options.type == 'initrd':
                type = 'initrd'
                
        if self.options.nodegrp:
            # Generate the node group
            imgfun.makeInitrd(self.options.nodegrp, image, type)
            
        else:
            # Missing node group name
            self.stdoutMessage('buildimage_need_a_node_group\n')
            sys.exit(-1)

            


        
if __name__ == '__main__':
    app = BuildInitrdApp()
    app.run()
