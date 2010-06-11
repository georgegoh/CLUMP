
from command import Command

class NicCheckCommand(Command):
    """
    This is the command class for gathering information on the provisioning network
    """
    def __init__(self, receiver, configuredNicCount):
        super(NicCheckCommand, self).__init__()
        self._receiver = receiver
        self._configuredNicCount = configuredNicCount

        ## We gather information on the provisioning network interface, and exposes
        ## a tuple consisting of : (interface, properties)
        self.provisionInterfaceTuple = None
        self.publicInterfaceTuple = None

    def _interface_prompt(self, interfaces, properties, network_type):
        count = 1
        print "\nSelect one of the following interfaces to use for the %s network:" % network_type
        for interface in interfaces:
            if properties[interface]['ip'] is not None and properties[interface]['ip'].strip() != '':
                if network_type == 'public': 
                    print "\t %d) Interface: %s, Ip: %s, Netmask: %s " % (count, interface, properties[interface]['ip'], properties[interface]['netmask'])
                    count += 1
                elif network_type == 'provisioning':
                    print "\t %d) Interface: %s, Ip: %s, Netmask: %s " % (count, interface, properties[interface]['ip'], properties[interface]['netmask'])
                    count += 1
             
         # If we do not find any interface then exit
        if count == 1:
            self._quitMessage = "Kusu setup could not detect any statically configured network interfaces\n   for use as your public network. At least TWO statically configured network interfaces\n   are required to install Kusu."
            self._proceedStatus = False 
            return self._proceedStatus
        return True

    def _promptForNic(self, interfaces, properties, network_type):
        status = self._interface_prompt(interfaces, properties, network_type)
        if not status:
            return status, ()
        while True:
            try:
                value = int(raw_input("Enter the number corresponding to your selected interface: ")) - 1
                if value in range(0, len(interfaces)):
                    break
                else:
                    value = None
                    print "Invalid selection. Select a number that corresponds to an interface in the above list."
            except ValueError:
                    print "Invalid selection. Select a number that corresponds to an interface in the above list."

        return status, (interfaces[value], properties[interfaces[value]])


    def _promptForPublicNic(self):
        interfaces, properties = self._receiver.physicalInterfacesAndProperties
        if self.provisionInterfaceTuple:
            del properties[self.provisionInterfaceTuple[0]]
            interfaces.remove(self.provisionInterfaceTuple[0])
        return self._promptForNic(interfaces, properties, "public")


    def _promptForProvisioningNic(self):
        interfaces, properties = self._receiver.physicalInterfacesAndProperties
        return self._promptForNic(interfaces, properties, "provisioning")


    def execute(self):

        self.singleNicInstall = False

        status, self.provisionInterfaceTuple = self._promptForProvisioningNic()
        if not status:
            return

        #if we have more than one configured nic, we prompt for whether the user want's to configure 
        # a second/public nic.
        if self._configuredNicCount > 1 and self.getYesNoAsBool("    Would you like to configure a public network"):

            status, self.publicInterfaceTuple = self._promptForPublicNic()
            if not status:
                return
        else:
            self.singleNicInstall = True

        self._proceedStatus = True

