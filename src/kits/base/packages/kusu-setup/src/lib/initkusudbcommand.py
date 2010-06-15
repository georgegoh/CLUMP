

from command import Command
import message

class InitKusuDBCommand(Command):
    """
    This is the command class for inializing kusudb
    """
    def __init__(self, receiver, nicCheck, dhcpCheck, envCheck, systemSettings):


        self._receiver = receiver
        self._nicCheck = nicCheck
        self._dhcpCheck = dhcpCheck
        self._envCheck = envCheck
        self._systemSettings = systemSettings

    def execute(self):
        #FIXME: log instead message.display("Initialising Kusu database settings")

        result = self._receiver.createDB(self._nicCheck, self._dhcpCheck, self._envCheck, self._systemSettings)

        if result:
            self._proceedStatus = True
            #message.success()
        else:
            self._proceedStatus =False
            self._quitMessage = "Failed to initialized kusudb database. Exiting..."
