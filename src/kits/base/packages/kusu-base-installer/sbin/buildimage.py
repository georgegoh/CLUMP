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

# This is the location for any user provided customization scripts
# Any changes to this must also be made in the rc.kusu.sh script.
KUSUUSCRIPTS='/etc/rc.kusu.custom.d'

# This is the script to run the post installation scripts
# Any changes to this must be made in the base kit.
KUSUPOSTSCRIPT='/etc/rc.kusu.sh'

import os
import sys
from optparse import OptionParser
from kusu.kusuapp import KusuApp
from kusu.kusudb import KusuDB



class BuildImage:
    """This class will provide the image management functions"""

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
        self.packages    = []     # A list of all the packages to include
        self.ostype      = ''     # The ostype for the repository
        self.kernel      = ''     # The name of the kernel to use from db
        self.gettext     = 0
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

        
    def makeImage(self, nodegroup, image):
        """makeImage - This method will create a image for a given node group.
        It will optionally name the image."""

        if not self.__validateNG(nodegroup):
            if self.stderrout:
                self.stderrout("ERROR: Invalid node group: %s\n", nodegroup)
            return

        self.__getPackages()
        self.__mkImageDir()
        self.__getRepoInfo()
        self.__prepYum()

        # Now install all the packages.  Note list of packages may exceed
        # length of args.
        arg = ''
        yumconf = os.path.join(self.imagedir, 'etc/yum.conf')
        try:
            for package in self.packages:
                arg = arg + " %s" % package
                if len(arg) > 8000:
                    # Call yum to install the packages
                    os.system('yum -y -t -d 2 -c \"%s\" --installroot \"%s\" install %s' % (yumconf, self.imagedir, arg))
                    arg = ''
            if len(arg):
                os.system('yum -y -t -d 2 -c \"%s\" --installroot \"%s\" install %s' % (yumconf, self.imagedir, arg))
                print ""
        except:
            if self.stderrout:
                self.stderrout("ERROR: Yum Failed!\n")

        # Do the post processing
        self.__runPostScripts()

        # Cleanup the installation fragments
        self.__cleanImage()

        # Package the image for use
        self.__packageImage()
        

    def __validateNG(self, nodegroup):
        """__validateNG - Test the node group name to make sure it is valid.
        Returns:  True - when the node group exists, otherwise False.
        It will also set the self.ngid to the value from the database."""
        query = ('select ngid, repoid, installtype, kernel from nodegroups '
                 'where ngname="%s"' % nodegroup )
        try:
            self.db.execute(query)
            data = self.db.fetchone()
        except:
            return False
        if data:
            self.ngid, self.repoid, self.installtype, self.kernel = data
            self.nodegroup = nodegroup
            return True
        return False


    def __mkImageDir(self):
        """__mkImageDir - get the name of the directory to store the image in
        and make that directory."""
        idir = self.db.getAppglobals('ImageBaseDir')
        if not idir:
            idir = '/depot/images'

        self.imagedir = os.path.join(idir, self.nodegroup)
        if not os.path.exists(idir):
            os.system('mkdir -p \"%s\"' % idir)
            
        if os.path.exists(self.imagedir):
            if self.stdoutout:
                self.stdoutout("Removing: %s\n", self.imagedir)
            os.system('rm -rf \"%s\"' % self.imagedir)
            
        os.mkdir(self.imagedir, 0700)
        


    def __getPackages(self):
        """__getPackages - Returns a list of packages and components that this
        image should contain."""

        # Get the list of all the optional packages to add.
        self.packages = []
        query = ('select packagename from packages where ngid="%s"' % self.ngid)
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            if self.stderrout:
                self.stderrout("DB_Query_Error: %s\n", query)
                
            sys.exit(-1)

        if data:
            for row in data:
                self.packages.append(row[0])

        # Add all the components to the list of packages
        query = ('select packagename from packages where ngid="%s"' % self.ngid)
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            if self.stderrout:
                self.stderrout("DB_Query_Error: %s\n", query)
                
            sys.exit(-1)

        if data:
            for row in data:
                self.packages.append(row[0])


    def __getRepoInfo(self):
        """__getRepoInfo - Gather the info for the repo we are going to use.
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


    def __prepYum(self):
        """__prepYum - prepare the image directory to run yum"""

        neededdirs = { 'bin' : 0755, 'lib' : 0755, 'tmp' : 0777,
                       'dev' : 0755, 'etc' : 0755, 'var' : 0755
                       }

        yumhost = self.db.getAppglobals('PrimaryInstaller')
        
        for dir,perms in neededdirs.items():
            os.mkdir(os.path.join(self.imagedir, dir), perms)

        # Make the second level directories.  This is not done in the upper code
        # because the dictionary does not guarentee the order in which they come out.
        neededdirs = { 'etc/sysconfig' : 0755, 'var/lib' : 0755,
                       'var/log' : 0755 }
        for dir,perms in neededdirs.items():
            os.mkdir(os.path.join(self.imagedir, dir), perms)

        neededdirs = { 'var/lib/rpm' : 0755
                       }
        for dir,perms in neededdirs.items():
            os.mkdir(os.path.join(self.imagedir, dir), perms)
            

        os.system('rpm --initdb --dbpath \"%s/var/lib/rpm\"' % self.imagedir)
        os.system('touch \"%s/etc/fstab\"' % self.imagedir)
        os.system('mknod \"%s/dev/null\" c 1 3 >/dev/null 2>&1' % self.imagedir)

        # print "repoid = %s" % self.repoid
        # print "repodir = %s" % self.repodir

        dirname = 'Redhat'
        if self.ostype[:6] == 'fedora':
            dirname = 'Fedora'
        if self.ostype[:4] == 'rhel' :
            dirname = 'Redhat'
        if self.ostype[:6] == 'centos':
            dirname = 'CentOS'

        # Create the yum config file
        yumconf = os.path.join(self.imagedir, 'etc/yum.conf')
        fp = file(yumconf, 'w')
        out = ( '[main]\n'
                'cachedir=/var/cache/yum\n'
                'debuglevel=2\n'
                'logfile=/var/log/yum.log\n'
                'reposdir=/dev/null\n'
                'tolerant=1\n\n'
                '[base]\n'
                'name=RHEL-%s - Base\n'
                'baseurl=http://%s/repos/%s/%s/RPMS/\n' % (self.ostype, yumhost, self.repoid, dirname)
                )

        fp.write(out)
        fp.close()



    def __runPostScripts(self):
        """__runPostScripts - This method copies any custom post installation
        scripts to the node.  It then chroots into the system and runs the kit
        post installation scripts.  It then runs the custom scripts"""

        print "Running post installation script(s)"

        # Copy Passwd and shadow
        os.system('cp /etc/passwd \"%s/etc/passwd\"' % self.imagedir)
        os.system('cp /etc/shadow \"%s/etc/shadow\"' % self.imagedir)

        # Create the initial /etc/fstab entry
        fstabent = []
        fstabent.append('# Created by buildimage.  Append your own lines\n')
        fstabent.append('devpts\t\t\t/dev/pts\t\tdevpts\tgid=5,mode=620\t0 0\n')
        fstabent.append('tmpfs\t\t\t/dev/shm\t\ttmpfs\tdefaults\t0 0\n')
        fstabent.append('proc\t\t\t/proc\t\tproc\tdefaults\t0 0\n')
        fstabent.append('sysfs\t\t\t/sys\t\tsysfs\tdefaults\t0 0\n')
        fp = open('%s/etc/fstab' % self.imagedir, 'w')
        fp.writelines(fstabent)
        fp.close()
        
        query = ('select script from scripts where ngid="%s"' % self.ngid)
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            if self.stderrout:
                self.stderrout("DB_Query_Error: %s\n", query)
            sys.exit(-1)

        if data:
            # Copy the script over
            global KUSUUSCRIPTS
            # sloc = os.path.join(self.imagedir, KUSUUSCRIPTS)   # This line failed!
            sloc = "%s/%s" % (self.imagedir, KUSUUSCRIPTS)
            for line in data:
                script = line[0]
                #print "imagedir=%s, sloc=%s, script=%s" % (self.imagedir, sloc, script)
                os.system('cp -f \"%s\" \"%s\"' % (script, sloc))
                newname = os.path.join(sloc,  os.path.basename(script))
                os.chmod(newname, 0755)
                if self.stdoutout:
                    self.stdoutout("Adding script: %s\n", script)
                

        global KUSUPOSTSCRIPT
        pscript = "%s/%s" % (self.imagedir, KUSUPOSTSCRIPT)
        if os.path.exists(pscript):
            if self.stdoutout:
                self.stdoutout("Chroot'ing to run script(s) in: %s\n" % self.imagedir)

            os.system('chroot \"%s\" %s' % (self.imagedir, KUSUPOSTSCRIPT))
        else:
            if self.stderrout:
                self.stderrout("WARNING:  The base kit is not installed\n")


    def __cleanImage(self):
        """cleanImage - Removes all the junk left over from the image creation
        process."""
        if self.ostype[:6] == 'fedora' or self.ostype[:4] == 'rhel' or self.ostype[:6] == 'centos':
            os.chdir(self.imagedir)
            os.system('rm -rf var/cache/yum/base/packages/*.rpm')
            print 'Removing:  \"%s/var/cache/yum/base/packages/*.rpm\"' %  self.imagedir

            
    def __packageImage(self):
        """__packageImage  - Package the image into a tar.bz2 file for use
        by the installing nodes."""
        if self.stdoutout:
            self.stdoutout("Compressing Image.  This will take some time.  Please wait\n")

        os.chdir(self.imagedir)
        os.system('tar cfj \"../%s.img.tar.bz2\" .' % self.ngid )
        os.system('chown apache:apache \"../%s.img.tar.bz2\"' % self.ngid )
        os.chdir('/tmp')
        os.system('rm -rf \"%s\"' %  self.imagedir)





class BuildImageApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)


    def toolVersion(self):
        """toolVersion - provide a version screen for this tool."""
        global version
        self.stdoutMessage("Version %s\n", self.version)
        sys.exit(0)


    def toolHelp(self):
        """toolHelp - provide a help screen for this tool."""
        self.stdoutMessage("buildimage_Help")
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
        self.parser.add_option("-v", "--version", action="store_true",
                               dest="wantver", default=False)

        (self.options, self.args) = self.parser.parse_args(sys.argv)

            

    def run(self):
        """run - Run the application"""
        self.parseargs()
        image = ''

        imgfun = BuildImage()
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

        if self.options.nodegrp:
            # Generate the node group
            imgfun.makeImage(self.options.nodegrp, image)
            
        else:
            # Missing node group name
            self.stdoutMessage('buildimage_need_a_node_group\n')
            sys.exit(-1)

            


        
if __name__ == '__main__':
    app = BuildImageApp()
    app.run()
