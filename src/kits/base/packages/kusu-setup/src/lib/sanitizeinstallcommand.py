

from command import Command
import message

class SanitizeInstallCommand(Command):
    """
    This is the command class for the pre-install cleanup task
    """
    def __init__(self, receiver):
        super(SanitizeInstallCommand, self).__init__()
        self._receiver = receiver

    def execute(self):
        detected = self._receiver.detectOldKusu()
        self._proceedStatus = True

        if (detected):
            print ("\n\n")
            print ("    ********************** WARNING **********************")
            print("    Kusu is already installed on this machine. \n    Proceeding will completely remove the current installation.")
                      
            if not self.getYesNoAsBool("    Would you like to proceed?"):
                self._proceedStatus = False
                self._quitMessage = "User abort. Exiting..." 
            else:
                self._receiver.cleanup()
                    
 
