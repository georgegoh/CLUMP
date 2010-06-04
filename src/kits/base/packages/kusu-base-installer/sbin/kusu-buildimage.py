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

# This file is used to determine if the base kit is installed
KUSUBASEFILE='/opt/kusu/sbin/cfmd'

import os
import shutil
import sys
from optparse import OptionParser
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB
from kusu.core import database

from primitive.system.software.dispatcher import Dispatcher
from primitive.system.software.probe import OS
from path import path
from kusu.util.errors import YumFailedToRunError
import subprocess

RHELFAMILY = ['rhel', 'centos', 'scientificlinux', 'scientificlinuxcern']

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
 
        self.apacheuser, self.apachegrp = Dispatcher.get('webserver_usergroup')
       
        engine = os.getenv('KUSU_DB_ENGINE', 'postgres')
        self.dbs = database.DB(engine, db='kusudb',username='apache')

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

        if self.installtype == 'package':
            if self.stderrout:
                self.stderrout("ERROR: Invalid node group type: %s\n", self.installtype)
            return

        ng = self.dbs.NodeGroups.select_by(ngname = nodegroup)[0]
        if not ng.repo:
            self.stdoutout('Nodegroup %s has no repo.\n' % ng.ngname)
            sys.exit(0)

        _os = ng.repo.os
        self.os_tup = (_os.name, _os.major, _os.arch)

        # Skip kusu-buildimage for opensuse
        if _os.name.lower() in ['opensuse', 'suse']:
            self.stdoutout('Skipping kusu-buildimage for %s distribution\n' % _os.name)
            sys.exit(0)

        system_arch = OS()[2].lower()
        if system_arch == 'i386' and _os.arch == 'x86_64':
            self.stdoutout('Skipping kusu-buildimage for %s. Unable to build on %s platform.\n' % (_os.arch, system_arch))       
            sys.exit(0)

        self.__getPackages()
        if len(self.packages) == 0:
            if self.stderrout:
                self.stderrout("ERROR: No packages selected for the image!\n")
            sys.exit(-1)
        
        self.__mkImageDir()
        self.__getRepoInfo()

        arg = ''

        if _os.name.lower() in ['sles']:
            os.system('echo y | /usr/bin/zypper --root %s service-add file://%s TEMPORARY > /dev/null 2>&1' % (self.imagedir, self.repodir))
            try:
                #Install some packages to enable 'network' service, for avoiding 'insserv error' while building image.
                prePkgs = ['aaa_base', 'sysconfig', 'dbus-1', 'hal', 'udev']
                os.system('echo y | zypper --root %s --non-interactive --no-gpg-checks install --auto-agree-with-licenses %s' % (self.imagedir, ' '.join(prePkgs)))
                for srv in ['boot.localnet', 'haldaemon', 'network']:
                    os.system('/sbin/insserv %s/etc/init.d/%s' % (self.imagedir, srv))

                for package in self.packages:
                    if package in prePkgs:
                        continue
                    arg = arg + " %s" % package
                    if len(arg) > 8000:
                        # Call zypper to install the packages
                        os.system('echo y | zypper --root %s --non-interactive --no-gpg-checks install --auto-agree-with-licenses %s' % (self.imagedir, arg))
                        arg = ''
                if len(arg):
                    os.system('echo y | zypper --root %s --non-interactive --no-gpg-checks install --auto-agree-with-licenses %s' % (self.imagedir, arg))
                    print ""
            except TypeError:
                if self.stderrout:
                    self.stderrout("ERROR: zypper Failed!\n")
        else:
            self.__prepYum()

            # Now install all the packages.  Note list of packages may exceed
            # length of args.
            yumconf = os.path.join(self.imagedir, 'tmp/yum.conf')
            try:
                for package in self.packages:
                    arg = arg + " %s" % package
                    if len(arg) > 8000:
                        # Call yum to install the packages
                        yt = os.system('yum -y -t -d 2 -c \"%s\" --installroot \"%s\" install %s' % (yumconf, self.imagedir, arg))
                        arg = ''
                    if yt:
                        raise YumFailedToRunError
                if len(arg):
                    yt = os.system('yum -y -t -d 2 -c \"%s\" --installroot \"%s\" install %s' % (yumconf, self.imagedir, arg))
                    print ""

                if yt:
                    raise YumFailedToRunError
            except:
                if self.stderrout:
                    self.stderrout("ERROR: Yum Failed!\n")

                if os.path.exists(self.imagedir):
                    self.stdoutout("Removing: %s\n", self.imagedir)
                    os.system('rm -rf \"%s\"' % self.imagedir)

                sys.exit(-1)

        # Do the post processing
        self.__runPostScripts()

        # Set Selinux policy
        self.__setPolicy(ng)
                
        # Cleanup the installation fragments
        self.__cleanImage()

        # Set up the diskless node
        self.__setupImage()

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

    def __setPolicy(self, ng):
        """ __setPolicy - Test kparams and set SE Linux policy. """

        kparams_selinux = [k.split('=') for k in ng.kparams.split() if k.startswith('selinux')]

        if kparams_selinux and '0' in kparams_selinux[0]:
            selinux_file = self.imagedir + '/etc/selinux/config'

            if not path(selinux_file).exists():
                if self.stderrout:
                    self.stderrout("WARNING: Selinux config file not found.. Continue with buildimage...")
                return     
            
            cmd = "sed --in-place -e 's/^SELINUX=enforcing$/SELINUX=DISABLED/' %s" %(selinux_file)
            run_cmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
            out, err = run_cmd.communicate()

            if run_cmd.returncode != 0:
                if self.stderrout:
                    self.stderrout("ERROR: Cannot set SE Linux policy.. Fatal Error... ")
                sys.exit(-1)

        return    

    def __mkImageDir(self):
        """__mkImageDir - get the name of the directory to store the image in
        and make that directory."""
        idir = self.db.getAppglobals('DEPOT_IMAGES_ROOT')
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
        query = ('select packagename from packages where ngid=%s' % self.ngid)
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
        if self.db.driver =='mysql':
            query = ('select cname from components c, ng_has_comp n, kits k where k.kid=c.kid and k.isOS=0 and n.cid=c.cid and ngid=%s' % self.ngid)
        else: #postgres
            query = ('select cname from components c, ng_has_comp n, kits k where k.kid=c.kid and k."isOS"=False and n.cid=c.cid and ngid=%s' % self.ngid)
        try:
            self.db.execute(query,postgres_replace=False)
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
                 'repos.repoid=nodegroups.repoid and ngid=%s' % self.ngid)
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

        neededdirs = { 'var/lib/rpm' : 0755, 'var/lib/yum' : 0755
                       }
        for dir,perms in neededdirs.items():
            os.mkdir(os.path.join(self.imagedir, dir), perms)
            
        os.system('rpm --initdb --dbpath \"%s/var/lib/rpm\"' % self.imagedir)
        os.system('touch \"%s/etc/fstab\"' % self.imagedir)
        os.system('mknod \"%s/dev/null\" c 1 3 >/dev/null 2>&1' % self.imagedir)

        dirname = Dispatcher.get('yum_repo_subdir', 'Server', os_tuple=self.os_tup)
        
        # Create the yum config file
        #yumconf = os.path.join(self.imagedir, 'etc/yum.conf')
        yumconf = os.path.join(self.imagedir, 'tmp/yum.conf')
        fp = file(yumconf, 'w')
        out = ( '[main]\n'
                'cachedir=/var/cache/yum\n'
                'debuglevel=2\n'
                'logfile=/var/log/yum.log\n'
                'reposdir=/dev/null\n'
                'tolerant=1\n\n'
                '[base]\n'
                'name=%s - Base\n'
                'baseurl=file://%s%s\n' % (dirname, self.repodir, dirname)
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
        fstabent.append('# Created by kusu-buildimage.  Append your own lines\n')
        fstabent.append('devpts\t\t\t/dev/pts\t\tdevpts\tgid=5,mode=620\t0 0\n')
        fstabent.append('tmpfs\t\t\t/dev/shm\t\ttmpfs\tdefaults\t0 0\n')
        fstabent.append('proc\t\t\t/proc\t\tproc\tdefaults\t0 0\n')
        fstabent.append('sysfs\t\t\t/sys\t\tsysfs\tdefaults\t0 0\n')
        fp = open('%s/etc/fstab' % self.imagedir, 'w')
        fp.writelines(fstabent)
        fp.close()
        
        query = ('select script from scripts where ngid=%s' % self.ngid)
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
            CUSTOMSCRIPTDIR = self.db.getAppglobals('DEPOT_REPOS_CUSTOM_SCRIPTS')
            if not CUSTOMSCRIPTDIR: CUSTOMSCRIPTDIR = '/depot/repos/custom_scripts'
            # sloc = os.path.join(self.imagedir, KUSUUSCRIPTS)   # This line failed!
            sloc = "%s/%s" % (self.imagedir, KUSUUSCRIPTS)
            for line in data:
                sfile = "%s/%s" % (CUSTOMSCRIPTDIR, line[0])
                #print "imagedir=%s, sloc=%s, script=%s" % (self.imagedir, sloc, sfile)
                os.system('cp -f \"%s\" \"%s\"' % (sfile, sloc))
                newname = os.path.join(sloc,  os.path.basename(sfile))
                os.chmod(newname, 0755)
                if self.stdoutout:
                    self.stdoutout("Adding script: %s\n", sfile)
                
        global KUSUBASEFILE
        if not os.path.exists(KUSUBASEFILE):
            if self.stderrout:
                self.stderrout("WARNING:  The base kit is not installed\n")


    def __cleanImage(self):
        """cleanImage - Removes all the junk left over from the image creation
        process."""
        if self.ostype[:6] == 'fedora' or self.ostype[:4] == 'rhel' or self.ostype[:6] == 'centos':
            os.chdir(self.imagedir)
            os.system('rm -rf var/cache/yum/base/packages/*.rpm')
            print 'Removing:  \"%s/var/cache/yum/base/packages/*.rpm\"' %  self.imagedir
            os.system('rm -f tmp/yum.conf')
            print 'Removing:  \"%s/tmp/yum.conf\"' %  self.imagedir

            
    def __packageImage(self):
        """__packageImage  - Package the image into a tar.bz2 file for use
        by the installing nodes."""
        if self.stdoutout:
            self.stdoutout("Compressing Image.  This will take some time.  Please wait\n")

        os.chdir(self.imagedir)
        if path('%s/proc' % self.imagedir).glob('*'):
            os.system('umount %s/proc' % self.imagedir)
        os.system('tar cfj \"../%s.img.tar.bz2\" .' % self.ngid )
        os.system('chown %s:%s \"../%s.img.tar.bz2\"' % (self.apacheuser, self.apachegrp, self.ngid))
        os.chdir('/tmp')
        os.system('rm -rf \"%s\"' %  self.imagedir)

    def __setupImage(self):
        
        # setup root ssh keys
        sshdir = os.path.join(self.imagedir, 'root/.ssh')
        if not os.path.exists(sshdir):
            os.makedirs(sshdir)
            os.chown(sshdir, 0, 0)
            os.chmod(sshdir, 0700)

            if os.path.exists('/root/.ssh/id_rsa.pub'):
                authorizedkeys =  os.path.join(sshdir, 'authorized_keys')
                shutil.copy('/root/.ssh/id_rsa.pub', os.path.join(sshdir, authorizedkeys))
                os.chown(authorizedkeys, 0, 0)
                os.chmod(authorizedkeys, 0644)

        # set up /etc/sysconfig/kernel for ticket 145644: After repopatch, imaged node does not set to boot from the new kernel.
        # We should be aware that this fix is only for RHEL. If we want to support SLES image in future,
        # we should notice /etc/sysconfig/kernel for RHEL and SLES is quite different.
        if self.os_tup[0] in RHELFAMILY:
            self.__createRHKconfig()

    def __createRHKconfig(self):
        
        # set up /etc/sysconfig/kernel for RHEL image file.
        kconfigdir = os.path.join(self.imagedir, 'etc/sysconfig')
        kconfigfile = os.path.join(kconfigdir, 'kernel')
        if not os.path.exists(kconfigdir):
            os.makedirs(kconfigdir)
            os.chown(kconfigdir, 0, 0)
            os.chmod(kconfigdir, 0755)
 
        f = open(kconfigfile, 'w+')
        f.write("# UPDATEDEFAULT specifies if new-kernel-pkg should make\n"
                "# new kernels the default\n")
        f.write("UPDATEDEFAULT=yes\n")
        f.write("\n")
        f.write("# DEFAULTKERNEL specifies the default kernel package type\n")
        f.write("DEFAULTKERNEL=kernel\n")
        f.close()


class BuildImageApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)
            
    def toolVersion(self):
        """toolVersion - provide a version screen for this tool."""
        global version
        self.stdoutMessage("kusu-buildimage version %s\n", self.version)
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

        # Check if root user
        if os.geteuid():
            print self._("nonroot_execution\n")
            sys.exit(-1)


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
