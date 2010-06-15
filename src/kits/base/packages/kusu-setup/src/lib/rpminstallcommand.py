

from command import Command
import os
import message

class RpmInstallCommand(Command):
    def __init__(self, receiver, repoid):
        self._receiver = receiver
        self._repoid = repoid

    def execute(self):

        #installLocation = "/mnt//base" #FIXME:
        #installLocation = raw_input("Please enter location of Kusu RPMs: [/media/cdrom] ")


        #if not os.path.exists(installLocation):
        #    self._proceedStatus = False
        #    self._quitMessage = "Invalid install location provided. Exiting..."
        #    return

        #if not self._receiver.verifyKusuDistroSupported(installLocation):
	    #self._proceedStatus = False
        #    self._quitMessage = "Kusu RPMs provided are not OS-compatible with the Installer machine."
        #    return

        message.display("Installing Kusu RPMs")
        status = self._receiver.installRPMs(self._repoid)

        if status:
            message.success()
            self._proceedStatus = True
        else:
            message.failure()
            self._proceedStatus = False
            self._quitMessage = "RPM Installation failed. Exiting." 

