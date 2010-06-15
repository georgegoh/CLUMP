

from command import Command
import message

RECOMMENDED_RAM_SIZE = 2048

class RamCheckCommand(Command):
    """
    This is the command class for checking requisite amount of RAM in the system
    """
    def __init__(self, receiver):
        self._receiver = receiver

    def execute(self):
        """
            By default we require the master node to have at least 2Gb RAM
        """ 

        message.display("Checking if at least 2GB of RAM is present")
        ramSize = self._receiver.ramSize
        if ramSize >= RECOMMENDED_RAM_SIZE:
            message.success()
            self._proceedStatus = True
        else:
    
            self._proceedStatus = False
            self._quitMessage = "\n    Insufficient memory for a master node installation.\n    At least 2GB is required. You have only %dMb available" % int(ramSize)

        
