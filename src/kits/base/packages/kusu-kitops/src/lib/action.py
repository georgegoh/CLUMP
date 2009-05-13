class KitopsAction(object):
    """Head of class hierarchy implementing actions on kits.

       Descendants of this class implement actions such as adding, updating or
       removing kits."""

    def __init__(self, koinst):
        """Create a KitopsAction instance.

           koinst is an instance of KitOps"""

        super(KitopsAction, self).__init__()

        self.koinst = koinst

    def run(self):
        """Perform the action."""

        raise NotImplementedError
