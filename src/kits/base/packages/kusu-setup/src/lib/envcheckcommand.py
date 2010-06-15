

from command import Command
from setup_errors import KusuProbePluginError
import message

class EnvCheckCommand(Command):
    """
    This is the command class for checking/probing for timestamp, language, FQDN and Keyboard
    """
    def __init__(self, provisioningInterfaceTuple, publicInterfaceTuple, fqdn_receiver):

        super(EnvCheckCommand, self).__init__()

        (self._prov_interface, self._prov_interface_props) = provisioningInterfaceTuple

        if publicInterfaceTuple is not None:
            (self._pub_interface, self._pub_interface_props) = publicInterfaceTuple

        self._fqdn_receiver = fqdn_receiver

    def execute(self):

        try:
            (self.prov_fqdn, self.pub_fqdn) = self._fqdn_receiver.fqdn
            self._proceedStatus = True

        except KusuProbePluginError, msg:
            message.failure()
            self._proceedStatus = False
            self._quitMessage = "Failed to properly detect system settings [%s]. Quitting." % msg

