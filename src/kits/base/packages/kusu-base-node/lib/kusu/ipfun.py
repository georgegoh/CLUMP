#!/usr/bin/env python
#
# $Id$
#
# ipfun.py - A collection of functions for manipulating IP addresses

#   Copyright 2007 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#


import string
import os

def validIP(IP):
    """Test the IP address to see if it is a valid format.
    Returns:   0  - IP address is invalid.
               1  - IP address is good."""
    substr = string.split(IP, '.')
    if len(substr) != 4:
        return 0
    
    for num in substr:
        try:
            numval = string.atoi(num)
        except:
            return 0

        # Reject octets like '010', '001', '00'
        if num[0] == '0' and len(num) > 1:
            return 0
        
        if numval < 0 or numval > 255:
            return 0
        
    return 1
    

def ip2number(IP):
    """Converts an IPv4 address into 32bit number.
    The IP must pass the validIP() test prior to conversion.
    Returns:  The numeric equivalent of the IP address."""
    substr = string.split(IP, '.')
    numval = 0
    for num in substr:
        numval = (numval << 8) + string.atoi(num)

    return numval


def number2ip(number):
    """Converts a 32bit integer into a IPv4 address. 
    Returns: The IP address numerically equivalent to the number."""
    ip = ''
    byte1 = number & 0xff
    byte2 = (number & 0xff00) >> 8
    byte3 = (number & 0xff0000) >> 16
    byte4 = (number & 0xff000000) >> 24
    ip = "%i.%i.%i.%i" % (byte4, byte3, byte2, byte1)  
    return ip

                
def incrementIP(startIP, increment=1, subnet=''):
    """Increment/decrement the startIP by the increment value.
    Optionally test the generated IP to ensure it does not
    overflow the subnet.
    Returns: New IP address
    Raises:  Exception if IP address is not within the given subnet."""
    startIPnum = ip2number(startIP)
    newIPnum = startIPnum + increment
    
    if subnet != '' :
        # Perform additional tests for over/underflow
        subnetnum =  ip2number(subnet)
        minnum = startIPnum & subnetnum
        if newIPnum <= minnum :
            raise "IP address underflow.  %s + %i is a restricted address"

        maxnum = minnum + (subnetnum ^ 0xffffffff)
        if newIPnum >= maxnum :
            raise "IP address overflow.  %s + %i is a restricted address"

    return number2ip(newIPnum)


def onNetwork(network, subnet, ip, start_ip=None):
    """Determines if the given ip lies within the network.
    Requires the network address, an IP on that network, as well as
    the subnet mask. Optional parameter is the pcm network start_ip to
    respect the PCM network schema where two overlapping networks have
    the same network and subnet, but different starting ips."""
    try:
        netnum = ip2number(network)
        masknum = ip2number(subnet)
        ipnum = ip2number(ip)
        if start_ip:
            start_num = ip2number(start_ip)
    except:
        # Got garbage
        return False
    
    minnum = netnum & masknum
    maxnum = minnum + (masknum ^ 0xffffffff)
    if start_ip and start_ip > minnum:
        minnum = start_num - 1
    if ipnum > minnum and ipnum < maxnum:
        return True
    return False


def getNetwork(ip, subnet):
    """Returns the network address given an IP and the subnet mask"""
    netnum = ip2number(ip) & ip2number(subnet)
    return number2ip(netnum)


def getBroadcast(ip, subnet):
    """Returns the broadcast address given an IP and the subnet mask"""
    bcnum = ip2number(ip) | (~ip2number(subnet))
    return number2ip(bcnum)


def getMyIPs ():
    """Determine the IP address(es) and subnet masks of this machine.
    WARNING:  This uses ifconfig to find the IPs"""
    myips = []
    ifconfig = '/sbin/ifconfig'
    cmd = "%s |grep inet" % ifconfig
    for line in os.popen(cmd).readlines():
        bits = string.split(line)
        #print bits
        if bits[1][:5] == 'addr:':
            ip = bits[1][5:]
            if string.count(ip, '.') == 3:
                # Looks like an IP
                try:
                    # Find the mask
                    if bits[3][:5] == 'Mask:':
                        mask = bits[3][5:]
                        myips.append([ip, mask])
                except:
                    pass
    return myips


def bestIP (myIPs, ipList):
    """Determine which IP in the ipList are on the same network as 
    this machine.  The 'myIPs' is the list of IPs produced by the
    getMyIPs function.
    Returns a list of IPs from the ipList that are on the same 
    network as this machine, or an empty list."""
    onnet = []
    for ip in ipList:
        for network, subnet in myIPs:
            if onNetwork(network, subnet, ip):
                onnet.append(ip)
    return onnet

def getArpaZone(network, mask):
    """Get the parent class subnet and its arpa zone"""
    ipbytes = string.split(network, '.')
    maskbytes = string.split(mask, '.')

    if maskbytes[0] != '255':
        #x.0.0.0 classless A, user ensure the correctness
        arpazone = '%s' % ipbytes[0]
        net = '%s.0.0.0' % ipbytes[0]
    elif maskbytes[1] != '255':
        #255.x.0.0 class A and classless B
        arpazone = '%s' % ipbytes[0]
        net = '%s.0.0.0' % ipbytes[0]
    elif maskbytes[2] != '255':
        #255.255.x.0 class B and classless C
        arpazone = '%s.%s' % (ipbytes[1], ipbytes[0])
        net = '%s.%s.0.0' % (ipbytes[0], ipbytes[1])
    else:
        #255.255.255.x
        arpazone = '%s.%s.%s' % (ipbytes[2], ipbytes[1], ipbytes[0])
        net = '%s.%s.%s.0' % (ipbytes[0], ipbytes[1], ipbytes[2])

    if arpazone in ['0','255','0.0.127']:
        arpazone = None

    return arpazone, net 
                
    
def unittest():
    """This is a series of tests for the functions in this class to verify they work.
    """
    if True :
        testnum = 1
        # Positive Test Cases
        outstr = "Test validIP() #%i" % testnum
        ip = "1.2.3.4"
        if validIP(ip) != 1:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test validIP() #%i" % testnum
        ip = "255.255.255.255"
        if validIP(ip) != 1:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test validIP() #%i" % testnum
        ip = "0.0.0.0"
        if validIP(ip) != 1:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        # Negative Test Cases
        outstr = "Test validIP() #%i" % testnum
        ip = "1.2.3.4.5"
        if validIP(ip) == 1:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test validIP() #%i" % testnum
        ip = "1.2.3"
        if validIP(ip) == 1:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test validIP() #%i" % testnum
        ip = "Hello.There.Whats.Up"
        if validIP(ip) == 1:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test validIP() #%i" % testnum
        ip = "1.2.3.256"
        if validIP(ip) == 1:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test validIP() #%i" % testnum
        ip = "1.2.3.-1"
        if validIP(ip) == 1:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test ip2number() #%i" % testnum
        ip = "0.0.0.1"
        if ip2number(ip) != 1:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test ip2number() #%i" % testnum
        ip = "0.0.0.255"
        if ip2number(ip) != 255:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test ip2number() #%i" % testnum
        ip = "0.0.1.0"
        if ip2number(ip) != 256:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test ip2number() #%i" % testnum
        ip = "0.0.1.1"
        if ip2number(ip) != 257:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test ip2number() #%i" % testnum
        ip = "1.1.1.1"
        if ip2number(ip) != 16843009:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test ip2number() #%i" % testnum
        ip = "255.255.255.255"
        if ip2number(ip) != 4294967295 :
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test number2ip() #%i" % testnum
        ip = "0.0.0.1"
        if number2ip(1) != ip:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test number2ip() #%i" % testnum
        ip = "0.0.0.255"
        if number2ip(255) != ip:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test number2ip() #%i" % testnum
        ip = "0.0.1.0"
        if number2ip(256) != ip:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test number2ip() #%i" % testnum
        ip = "0.0.1.1"
        if number2ip(257) != ip:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test number2ip() #%i" % testnum
        ip = "1.1.1.1"
        if number2ip(16843009) != ip:
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test number2ip() #%i" % testnum
        ip = "255.255.255.255"
        if number2ip(4294967295) != ip :
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test incrementIP() #%i" % testnum
        ipin = "255.255.255.254"
        ipout = "255.255.255.255"
        if incrementIP(ipin) != ipout :
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test incrementIP() #%i" % testnum
        ipin = "255.255.255.250"
        ipout = "255.255.255.255"
        if incrementIP(ipin, 5) != ipout :
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test incrementIP() #%i" % testnum
        ipin = "255.255.255.255"
        ipout = "255.255.255.250"
        if incrementIP(ipin, -5) != ipout :
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test incrementIP() #%i" % testnum
        ipin = "1.2.250.255"
        ipout = "1.2.251.0"
        if incrementIP(ipin, 1) != ipout :
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test incrementIP() #%i" % testnum
        ipin = "1.2.251.0"
        ipout = "1.2.250.255"
        if incrementIP(ipin, -1) != ipout :
            outstr += " Fail"
        else :
            outstr += " Pass"
        print outstr
        testnum += 1

        outstr = "Test incrementIP() #%i" % testnum
        ipin = "1.2.255.250"
        ipout = ""
        try :
            incrementIP(ipin, 5, "255.255.0.0")
        except:
            outstr += " Pass"
        else:
            outstr += " Fail"
        print outstr
        testnum += 1

        outstr = "Test incrementIP() #%i" % testnum
        ipin = "1.2.255.250"
        ipout = ""
        try :
            incrementIP(ipin, 10, "255.255.0.0")
        except:
            outstr += " Pass"
        else:
            outstr += " Fail"
        print outstr
        testnum += 1

        outstr = "Test incrementIP() #%i" % testnum
        ipin = "1.2.0.5"
        ipout = ""
        try :
            incrementIP(ipin, -5, "255.255.0.0")
        except:
            outstr += " Pass"
        else:
            outstr += " Fail"
        print outstr
        testnum += 1

        outstr = "Test incrementIP() #%i" % testnum
        ipin = "1.2.0.5"
        ipout = ""
        try :
            incrementIP(ipin, -15, "255.255.0.0")
        except:
            outstr += " Pass"
        else:
            outstr += " Fail"
        print outstr
        testnum += 1

        outstr = "Test getMyIPs() #%i" % testnum
        try:
            m = getMyIPs()
        except:
            outstr += " Fail"
        else:
            outstr += " Pass"
        print outstr
        testnum += 1
        
        outstr = "Test getMyIPs() #%i" % testnum
        t = 1
        for data in m:
            outstr = "   Subtest #%i" % t
            ip, sm = data
            if not ip or not sm:
                outstr += " Fail"
            else:
                if validIP(ip) == 0 or validIP(sm) == 0:
                    outstr += " Fail"
                else:
                    outstr += " IP=%s Subnet=%s Pass" % (ip, sm)
            print outstr
            t += 1
        testnum += 1


        outstr = "Test bestIP()  #%i" % testnum
        myIPs = [['10.0.0.1', '255.0.0.0'], ['172.16.2.3', '255.255.0.0'], ['192.168.1.5', '255.255.255.0']]
        ipList = ['11.0.0.1', '173.16.2.3', '199.168.1.5']
        bestips = ['-none-']
        try:
            bestips = bestIP (myIPs, ipList)
        except:
            outstr += " Fail"
        else:
            outstr += " Pass"
        print outstr
        testnum += 1
        
        outstr = "Test bestIP()  (no matches)  #%i" % testnum
        if not bestips:
            outstr += " Pass"
        else:
            outstr += " Fail"
        print outstr
        testnum += 1

        outstr = "Test bestIP()  (one match)  #%i" % testnum
        myIPs = [['10.0.0.1', '255.0.0.0'], ['172.16.2.3', '255.255.0.0'], ['192.168.1.5', '255.255.255.0']]
        ipList = ['10.99.99.99', '173.16.99.99', '199.168.1.99']
        try:
            bestips = bestIP (myIPs, ipList)
        except:
            outstr += " Fail"
        else:
            if bestips[0] == '10.99.99.99':
                outstr += " Pass"
            else:
                outstr += " Fail"
        print outstr
        testnum += 1

        outstr = "Test bestIP()  (two match)  #%i" % testnum
        myIPs = [['10.0.0.1', '255.0.0.0'], ['172.16.2.3', '255.255.0.0'], ['192.168.1.5', '255.255.255.0']]
        ipList = ['10.99.99.99', '172.16.99.99', '199.168.1.99']
        try:
            bestips = bestIP (myIPs, ipList)
        except:
            outstr += " Fail"
        else:
            if bestips[0] == '10.99.99.99' and bestips[1] == '172.16.99.99':
                outstr += " Pass"
            else:
                outstr += " Fail"
        print outstr
        testnum += 1

        outstr = "Test bestIP()  (three match)  #%i" % testnum
        myIPs = [['10.0.0.1', '255.0.0.0'], ['172.16.2.3', '255.255.0.0'], ['192.168.1.5', '255.255.255.0']]
        ipList = ['10.99.99.99', '172.16.99.99', '192.168.1.99']
        try:
            bestips = bestIP (myIPs, ipList)
        except:
            outstr += " Fail"
        else:
            if bestips[0] == '10.99.99.99' and bestips[1] == '172.16.99.99' and bestips[2] == '192.168.1.99':
                outstr += " Pass"
            else:
                outstr += " Fail"
        print outstr
        testnum += 1



# Run the unittest if run directly
if __name__ == '__main__':
    unittest()
