from command import Command

class InstallOSKitCommand(Command):
    """
    This is the command class for prompting and installing the OS kit
    """
    def __init__(self, receiver):
        super(InstallOSKitCommand, self).__init__()
        self._receiver = receiver

    def execute(self):
        self._proceedStatus = False
        while True:
            try:
                value = int(raw_input('Select the media to install KUSU from: \n' +
                                      '1)\tCD/DVD drive \n' +
                                      '2)\tISO image or mount point\n' +
                                      '>> '))
            except:
                print "Invalid option is given."
                continue

            if value == 1:
                #Prompt for and install the additional kits
                raw_input ("Insert the CD/DVD media containing your KUSU Installation. Press ENTER to continue...")
                status, msg = self._receiver.installKitsOnBootMedia('cdrom')
            elif value == 2:
                status, msg = self._receiver.installKitsOnBootMedia('iso')
            else:
                print "Invalid option is given."
                continue

            if not status:
                print msg
                print "Installation can't continue until the 'base kit' has been installed"
                self._proceedStatus = False
            else:
                self._proceedStatus = True
                break

        #Prompt for and install the OS kit
        while True:
            try:
                value = int(raw_input('Select the media to install the OS kit from: \n' +
                                      '1)\tCD/DVD drive \n' +
                                      '2)\tISO image or mount point\n' +
                                      '>> '))
            except:
                print "Invalid option is given."
                continue

            if value == 1:
                #Prompt for and install the base kit
                raw_input ("Insert the CD/DVD media containing your OS. Press ENTER to continue...")
                status, msg = self._receiver.install_os_kit('cdrom')
            elif value == 2:
                status, msg = self._receiver.install_os_kit('iso')
            else:
                print "Invalid option is given."
                continue
            
            if not status:
                print msg
                print "Installation can't continue until the 'OS kit' has been installed"
                self._proceedStatus = False
            else:
                self._proceedStatus = True
                break

