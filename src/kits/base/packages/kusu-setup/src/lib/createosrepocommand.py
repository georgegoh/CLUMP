from command import Command

class CreateOSRepoCommand(Command):
    """
    This is the command class for inializing/creating the OS repository
    """
    def __init__(self, receiver):
        super(CreateOSRepoCommand, self).__init__()

        self._receiver = receiver

    def get_default_repo_name(self):
        return self._receiver.default_repo_name


    def get_default_repo_id(self):
        return self._receiver.default_repo_id

    def execute(self):

        self._proceedStatus = True

        try:
            self._receiver.makeRepo()
        except Exception, msg:
            self._proceedStatus = False
            self._quitMessage = msg

    default_repo_name = property(get_default_repo_name)
    default_repo_id = property(get_default_repo_id)
