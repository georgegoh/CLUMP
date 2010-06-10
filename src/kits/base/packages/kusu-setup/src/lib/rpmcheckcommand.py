

from command import Command
from string import upper
import message

#FIXME: This must be a build-time make macro
SUPPORTED_OPERATING_SYSTEMS = ['RHEL', 'CENTOS']

class RpmCheckCommand(Command):
    """
    This is the command class for pre-installation rpm compatibility check
    """
    def __init__(self, receiver):
        super(RpmCheckCommand, self).__init__()
        self._receiver = receiver
        self.distroName = None

    def execute(self):
        message.display("Checking for OS compatibility")

        if upper(self._receiver.distroName) in SUPPORTED_OPERATING_SYSTEMS:
            message.success()
            self._proceedStatus = True
            self.distroName = self._receiver.distroName
        else:
            #message.failure()
            self._proceedStatus = False
            self._quitMessage = "This operating system is not compatible with this installer."

        
