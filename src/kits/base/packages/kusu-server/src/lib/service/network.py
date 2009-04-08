import socket
import fcntl
import struct
import array
import kusu2
from primitive.system.hardware import net

class NetworkService:
    def __init__(self):
        pass


    def getInterfaces(self):

        ifaceMap = net.getPhysicalInterfaces()
        ifaceNames = []

        for iface in ifaceMap.keys():
            ifaceNames.append(iface)

        return ifaceNames

    def getInterfaceConfig(self, interfaceName):

        interfaces = net.getPhysicalInterfaces()
        netCfg = interfaces[interfaceName]

        #if (netCfg is None):
        #    throw new Exception("Invalid interface selected")
        cfg = kusu2.config.net.NetworkConfig() 
        cfg.ip = netCfg["ip"]
        cfg.name = interfaceName
        #cfg.network =
        cfg.netmask = netCfg["netmask"]
        #cfg.gateway =
        #cfg.dhcp = netCfg["dhcp"]
        #cfg.enabledOnBoot = enabledOnBoot

        return cfg

    def updateInterfaceConfig(self, config):
        #NOTE: This method copied and adapted from kusu-net-tool.
        #TODO: This just updates the network configuration. To apply these
        #      settings would require the network rc scripts to be re-run.

        #assert isinstance (config, NetworkConfig)
        network = ipfun.getNetwork(config.ip, config.netmask)

        bcast = ipfun.getBroadcast(config.ip, config.netmask)

        (fpdst, dstfile) = tempfile.mkstemp('', 'kusu-')

        filename = 'ifcfg-%s' % (config.name)

        srcfile = '/etc/sysconfig/network-scripts/%s' % (filename)

        bitmask = 0

        # Set a flag indicating whether or not the file exists before we
        # update/create the replacement
        bCfgExists = os.path.exists(srcfile)

        if bCfgExists:
            fpsrc = open(srcfile)

            for line in fpsrc:
                if re.compile("^BROADCAST=.*").match(line):
                    os.write(fpdst, "BROADCAST=%s\n" % (bcast))
                    bitmask |= CFG_BROADCAST
                    continue
                elif re.compile("^IPADDR=.*").match(line):
                    os.write(fpdst, "IPADDR=%s\n" % (config.ip))
                    bitmask |= CFG_IPADDR
                    continue
                elif re.compile("^NETMASK=.*").match(line):
                    os.write(fpdst, "NETMASK=%s\n" % (config.netmask))
                    bitmask |= CFG_NETMASK
                    continue
                elif re.compile("^NETWORK=.*").match(line):
                    os.write(fpdst, "NETWORK=%s\n" % (network))
                    bitmask |= CFG_NETWORK
                    continue
                elif re.compile("^HWADDR=.*").match(line):
                    bitmask |= CFG_HWADDR

                    (key, cur_hwaddr) = line.rstrip().split('=')

                    if config.macaddr and (config.macaddr != cur_hwaddr):
                        os.write(fpdst, "HWADDR=%s\n" % (config.macaddr.upper()))
                        continue

                elif re.compile("^DEVICE=.*").match(line):
                    bitmask |= CFG_DEVICE
                elif re.compile("^ONBOOT=.*").match(line):
                    bitmask |= CFG_ONBOOT
                elif re.compile("^BOOTPROTO=.*").match(line):
                    continue

                os.write(fpdst, line)

         # Add any missing netsettings
        if not (bitmask & CFG_DEVICE):
            os.write(fpdst, "DEVICE=%s\n" % (config.name))
        if not (bitmask & CFG_HWADDR):
            if config.macaddr:
                macaddr = config.macaddr.upper()
            else:
                # Attempt to determine MAC address for device
                macaddr = getMacAddress(config.name)

            if macaddr:
                os.write(fpdst, "HWADDR=%s\n" % (macaddr))
        if not (bitmask & CFG_BROADCAST):
            os.write(fpdst, "BROADCAST=%s\n" % (bcast))
        if not (bitmask & CFG_IPADDR):
            os.write(fpdst, "IPADDR=%s\n" % (config.ip))
        if not (bitmask & CFG_NETMASK):
            os.write(fpdst, "NETMASK=%s\n" % (config.netmask))
        if not (bitmask & CFG_NETWORK):
            os.write(fpdst, "NETWORK=%s\n" % (network))
        if not (bitmask & CFG_ONBOOT):
            # Enable any new interface by default
            os.write(fpdst, "ONBOOT=yes\n")

        os.close(fpdst)

        # Move source file to *.orig
        if bCfgExists:
            fpsrc.close()

            # Move the original file out of place; the RH network scripts
            # will safely ignore files with the ".orig" suffix
            shutil.move(srcfile, srcfile + '.orig')

        # Move new to original file name (ifcfg-xxx)
        shutil.move(dstfile, srcfile)


    def getDnsConfig(self):
        """
            /etc/resolv.conf information is currently being handled by genconfig resolv
            genconfig reads info from the database, then 
        """

        pass


    def listInterfaces(self):
        """
            This method returns a list of currently active network interfaces
            Code taken from: http://code.activestate.com/recipes/439093/
        """
        max_possible = 128  # arbitrary. raise if needed.
        bytes = max_possible * 32
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        names = array.array('B', '\0' * bytes)
        outbytes = struct.unpack('iL', fcntl.ioctl(
            s.fileno(),
            0x8912,  # SIOCGIFCONF
            struct.pack('iL', bytes, names.buffer_info()[0])
        ))[0]
        namestr = names.tostring()
        return [namestr[i:i+32].split('\0', 1)[0] for i in range(0, outbytes, 32)]
