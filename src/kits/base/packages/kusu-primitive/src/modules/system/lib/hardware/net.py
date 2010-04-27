import re
import os
import IPy
import subprocess
from path import path
from primitive.system.hardware.pci import PCI
from primitive.support import compat
from primitive.support.util import runCommand
from primitive.core.errors import ModuleException

def getAllInterfaces():
    sys_net = path('/sys/class/net/')

    d = {}
    for p in sys_net.dirs():
        intf = p.basename()
        n = Net(intf) 

        d[intf] = {}
        d[intf]['vendor'] = n.vendor
        d[intf]['device'] = n.device
        d[intf]['module'] = n.module
        d[intf]['isPhysical'] = n.isPhysical()
        d[intf]['hwaddr'] = n.mac
        d[intf]['ip'] = n.ip
        d[intf]['netmask'] = n.netmask
        d[intf]['dhcp'] = n.dhcp

        if n.isPhysical():
            d[intf]['pciBusInfo'] = n.pciBusInfo

    return d

def getPhysicalInterfaces():
    d = getAllInterfaces()

    dkeys = d.keys()

    # remove non-physical interfaces from dictionary
    for key in dkeys:
        if not d[key]['isPhysical']:
            d.pop(key)

    return d

def arrangeOnBoardNicsFirst(interfaces):
    """
    Given a dictionary of interfaces, rename the interfaces so
    that on-board nics come before the add-on nics.
    Returns the resulting dictionary.
    """
    on_board_list = []
    add_on_list = []
    for interface in sorted(interfaces):
        if os.system("biosdecode | grep 'Slot Entry' | grep '%s' | grep 'on-board' > /dev/null" % \
                interfaces[interface]['pciBusInfo'].lower()) == 0:
            mac = interfaces[interface]['hwaddr']
            on_board_list.append((mac, interface))
        else:
            # assume everything else is an add-on nic
            add_on_list.append(interface)

    new_interfaces = {}
    i = 0

    # If this is a Dell "PowerEdge 1950" or "PowerEdge 2950", sort on-board NICs by 
    # MAC address. This is needed because when those hardware are booted with SLES 10.3,
    # the interfaces are named incorrectly, i.e. on-board NIC1 is named eth1 while
    # on-board NIC2 is named eth0.
    # Sorting is done this way:
    # >>> on_board_list = [('08:00:27:be:46:b2', 'eth0'), ('08:00:27:be:46:b1', 'eth1')]
    # >>> on_board_list.sort()
    # on_board_list is now ('08:00:27:be:46:b1', 'eth1'), ('08:00:27:be:46:b2', 'eth0')]
    if os.system("dmidecode | grep 'Product Name:' | grep 'PowerEdge [12]950' > /dev/null") == 0:
        on_board_list.sort()

    for mac, interface in on_board_list:
        new_interfaces['eth%d' % i] = interfaces[interface]
        i += 1
    for interface in add_on_list:
        new_interfaces['eth%d' % i] = interfaces[interface]
        i += 1
    return new_interfaces

def getPhysicalAddressList():
    nets = getPhysicalInterfaces()

    macs = [x['hwaddr'] for x in nets.values()]

    return macs

#FIXME: change name to NetDevice()
class Net:
    sys_net = path('/sys/class/net/')

    interface = None
    vendor = None
    device = None
    module = None
    mac = None
    ip = None
    netmask = None
    dhcp = None

    def __init__(self, interface):
        if interface not in self._getInterfaces():
            raise Exception, 'Interface not found'

        self.interface = interface
        self.dev_path = self.sys_net / interface / 'device'    

        if self.isPhysical():
            self._getVendorDevice()
            self._getModule()
            self._getMAC()
            self._getIPNetmask()
            self._getDHCP()
            self._getPciBusInfo()

    def _getInterfaces(self):
        sys_net = path('/sys/class/net/')
        return [p.basename() for p in sys_net.dirs()]

    def isPhysical(self):
        if self.dev_path.exists():
            return True
        else:
            return False

    def _getVendorDevice(self):
        vendor_path = self.dev_path / 'vendor'
        f = open(vendor_path, 'r')
        vendor = f.read()
        f.close()
    
        device_path = self.dev_path / 'device'
        f = open(device_path, 'r')
        device = f.read()
        f.close()

        #f = open(dev_path / 'subsystem_device', 'r')
        #subsystem_device = f.read()
        #f.close()

        #f = open(dev_path / 'subsystem_vendor', 'r')
        #subsystem_vendor = f.read()
        #f.close()

        # Strip off 0x and \n
        vendor = vendor[2:].strip()
        device = device[2:].strip()
        #subsystem_device = subsystem_device[2:].strip()
        #subsystem_vendor = subsystem_vendor[2:].strip()

        self.pci = PCI([vendor])

        if self.pci.ids.has_key(vendor):
            self.vendor = self.pci.ids[vendor]['NAME']

            if self.pci.ids[vendor]['DEVICE'].has_key(device):
                self.device = self.pci.ids[vendor]['DEVICE'][device]['NAME']
   
    def _getModule(self):
        # Attempt /sys/class/net/<if>/driver symlink
        driver_path = path(self.sys_net / self.interface / 'driver')
        if driver_path.exists():
            self.module = driver_path.realpath().basename()
        else:
            # Attempt /sys/class/net/<if>/devce/driver symlink
            driver_path = self.dev_path / 'driver'
            if driver_path.exists(): 
                self.module = driver_path.realpath().basename()

    def _getMAC(self):
        address = '/sys/class/net/%s/address' % self.interface
        
        f = open(address, 'r')
        self.mac = f.read().strip()
        f.close()

    def _getIPNetmask(self):
        self.ip = None
        self.netmask = None
        cmd = ['ip', '-f', 'inet', 'addr', 'show', self.interface]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        info = p.communicate()[0]
        # if interface is not configured, then the ip command returns nothing.
        if not info:
            return

        # look for match of inet address pattern.
        match = re.search('inet\s[0-9./]+', info)
        if not match:
            return
    
        # look for first match.
        first_match = match.group(0)
        if not first_match:
            return

        # process second half of match, i.e., 'net/netmask'.
        ip_netmask_str = first_match.split()[1]
        li = ip_netmask_str.split('/')
        self.ip = li[0]
        n = IPy.IP('0.0.0.0/%s' % li[1])
        netmask = n.netmask()
        self.netmask = str(netmask)

    def _getDHCP(self):
        self.dhcp = False
        if not self.mac:
            self._getMAC()
        # Redhat style
        ifcfg = path('/etc/sysconfig/network-scripts/ifcfg-%s' % self.interface)
        # SLES style
        if not ifcfg.exists():
            ifcfg = path('/etc/sysconfig/network/ifcfg-eth-id-%s' % self.mac)
        # OpenSUSE style
        if not ifcfg.exists():
            ifcfg = path('/etc/sysconfig/network/ifcfg-%s' % self.interface)
        if not ifcfg.exists():
            return

        f = ifcfg.open('r')
        lines = f.readlines()
        for line in lines:
            if line.strip()[0] == '#':
                continue
            try:
                key,val = line.split('=', 1)
                key = key.strip()
                val = val.strip()
            except:
                continue
            if key.lower() == 'bootproto':
                self.dhcp = (val.lower().strip("\'") == 'dhcp')

    def _getPciBusInfo(self):
        """
        The result of path.readlink looks like this:
          '../../../devices/pci0000:00/0000:00:03.0'
        We only want the '00:03' bit (and in lower-case).
        """
        self.pciBusInfo = str(self.dev_path.readlink()).split('/')[-1][5:-2].lower()

    def genIntfConf(self, template,aux_inputs,**args):
        '''Generate a network IF script for various distribution based on a template'''
        from primitive.configtool.commands import ConfigCommand
        from primitive.configtool.plugins import BasePlugin

        class IntfPlugin(BasePlugin):
            ''' Simple class just cascades template and arguments to cheetah'''
            def validateArgs(self,args_dict):
                pass

        inputs = { 'name' : '',
                   'template'  : template,
                   'plugin' : IntfPlugin,
                   'plugin_args' : args }
        inputs.update(aux_inputs) # grab any auxillary inputs

        t = ConfigCommand(**inputs)
        output_str = t.execute()

        return output_str 
