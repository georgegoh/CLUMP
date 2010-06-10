import os, tempfile
from path import path
from primitive.support.rpmtool import RPM
from kusu.kitops.kitops import KitOps
from bootstrap.setup.installerinitreceiver import InstallerInitReceiver

from primitive.system.software import probe as softprobe

try:
    import subprocess
except:
    from popen5 import subprocess

FIND_COMMAND = 'find -P %s -name kit-base*.rpm'
SUPPORTED_DISTROS = ['rhel', 'centos']

class RpmInstallReceiver:
    def __init__(self):

        self._rhel_repoTemplate = '''[bootstraprepo]
name=BootstrapRepo
baseurl=file://///depot/repos/%s/Server
enabled=1
gpgcheck=0
'''

        self._centos_repoTemplate = '''[bootstraprepo]
name=BootstrapRepo
baseurl=file://///depot/repos/%s
enabled=1
gpgcheck=0
'''

    def installRPMs(self, repoid):
        """
            Install RPMs from local repository
        """

        name, ver, arch = softprobe.OS() 

        distro = name.lower()
 
        if distro == 'rhel':
            repoText = self._rhel_repoTemplate % repoid
        elif distro == 'centos':
            repoText = self._centos_repoTemplate % repoid
            
        #generate a tempfile for our yum config
        yum_file = tempfile.NamedTemporaryFile(mode='w')
        yum_file.file.writelines(repoText)
        yum_file.flush()

        yumCmd = subprocess.Popen("yum -c %s -y install component-base-installer component-base-node component-gnome-desktop" % yum_file.name, shell=True, stdout=subprocess.PIPE)
        result, code = yumCmd.communicate()

        yum_file.close()

        #Loop until we have an exit status from YUM
        #Potentially harmful if YUM screws us
        while yumCmd.returncode is None:
            continue

        return yumCmd.returncode == 0 #assume success if returncode == 0

    def verifyKusuDistroSupported(self, basedir):
        kit_rpm_path = self.retrieveKitRPM(basedir)
        if path(kit_rpm_path).exists():
            kit_rpm = RPM(kit_rpm_path)
            kops = KitOps()
            kit, component = kops.getKitRPMInfo(kit_rpm)
            return self.verifyRPMDistro(component)
        else:
            print "kit-base RPM cannot be found. Please check the location of KUSU RPMS."
            return False

    def retrieveKitRPM(self, basedir):
        basedir = path(basedir)
        if basedir.exists():
            cmd = FIND_COMMAND % basedir
            fCmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            out, err = fCmd.communicate()
            if out:
                return out.rstrip('\n')
        
    def verifyRPMDistro(self, kit_info_component):
        if kit_info_component[0]['name'] == 'component-base-installer':
            base_os = kit_info_component[0]['os']
            base_os_name = base_os[0]['name']
            installer = InstallerInitReceiver()
            if installer.distroName.lower() in SUPPORTED_DISTROS and base_os_name == 'rhelfamily':
                return True
