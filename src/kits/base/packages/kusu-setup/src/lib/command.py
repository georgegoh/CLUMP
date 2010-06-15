
class Command(object):
    
    def __init__(self):
        self._proceedStatus = False
        self._quitMessage = ""

    def execute(self):
       pass

    def getYesNoAsBool(self, prompt):
        answer = "INITIAL_PROMPT"

        #force a single-character Yes/No response
        while answer.strip().lower() not in ['no', 'yes', 'y', 'n', '']:
            answer = raw_input("%s ? (Y/[N])" % prompt)

        if answer.strip().lower() in ['yes','y']:
            return True

        return False

    def getQuitMessage(self):
        """
            The reason for quitting
        """
        return self._quitMessage


    def getProceedStatus(self):
        """
            This determines whether our caller can proceed with the next call or not
            _proceedStatus = True - Proceed
            _proceedStatus = False - Halt and get reason from quitMessage property
        """
        return self._proceedStatus

    ## Define our properties
    quitMessage = property(getQuitMessage)
    proceedStatus =  property(getProceedStatus)
