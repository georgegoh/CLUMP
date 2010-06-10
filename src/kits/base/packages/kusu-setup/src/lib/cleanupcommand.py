

from command import Command

class CleanupCommand(Command):
    def __init__(self, receiver):
        self._receiver = receiver

    def execute(self):
        print ("Cleaning up partial Kusu installation...")
        self._receiver.cleanup()
        


