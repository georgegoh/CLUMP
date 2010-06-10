
from command import Command
from primitive.system.software import probe
import message

class SELinuxCheckCommand(Command):
    def __init__(self):
        super(SELinuxCheckCommand, self).__init__()
        
    def execute(self):
        
        message.display("Checking if SELinux is disabled")
        
        if probe.getSelinuxStatus():
            self._proceedStatus = False
            self._quitMessage = "\n   SELinux is enabled. Kusu cannot be installed on a system\n   with SELinux enabled. Please disable SELinux and restart\n   the kusu-setup installation.\n   NOTE: A system restart may be required after disabling SELinux"
            
        else:
            self._proceedStatus = True
            message.success()
    
    
        
