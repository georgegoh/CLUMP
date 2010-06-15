from command import Command

class InstallExtraKitCommand(Command):
    """
    This is the command class for prompting and installing additional kits
    """
    def __init__(self, receiver):
        super(InstallExtraKitCommand, self).__init__()
        self._receiver = receiver
 
    def execute(self):
        self._prompt_for_additional_kit()
    
    def _prompt_for_additional_kit(self):
        
        while True:
            value = raw_input('Do you want to add any additional kits[Y|N]: ')
            if value.lower() in ['y', 'yes']:
                try:
                    value = int(raw_input('Select the kit media to add the kit from: \n' +
                                          '1)\tCD/DVD drive \n' +
                                          '2)\tISO image or mount point\n' +
                                          '>> '))
                except:
                    print "Invalid option is given."
                    continue

                if value == 1:  
                    #Prompt for and install the additional kits
                    raw_input ("Insert the CD/DVD media containing your kits. Press ENTER to continue...")
                    status, msg = self._receiver.install_kits('cdrom')
                    if not status:
                        print msg
                elif value == 2:
                    status, msg = self._receiver.install_kits('iso')
                    if not status:
                        print msg
                else:
                    print "Invalid option is given."
                    continue
            elif value.lower() in ['n', 'no']:
                break 
            else:
                print "Wrong Input enter [Y|N]" 
                continue

        self._proceedStatus = True
