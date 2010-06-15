#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# $Id$
#
# pylint: disable-msg=C0103
#
# Module --------------------------------------------------------------------
# COPYRIGHT NOTICE
#
# © 2008 Platform Computing. All Rights Reserved.
# All other trademarks are the property of their respective
# holders.
#
# CREATED
#   Author: Pramod Dahale
#   Date:   2007/09/20
#
# LAST CHANGED
#   $Author: $
#   $Date: $
# ---------------------------------------------------------------------------

"""
This file is for power management of virtual machines
"""

import kusu.power
# Fixme: this requires ScaPylib
import scaerror
# Fixme: this requires ScaPylib
import scaremotecommand

vmcmd = '/usr/bin/vmware-cmd'

class vmpower(kusu.power.Plugin):
    """
    Manage VMPOWER power devices
    """
    # ----------------------------------------
    # Private functions
    # ----------------------------------------
    def __runCmd(self, node, options, command, opmode = None):
        """
        This function is to frame the command that is required to be to be executing 
        and also performs the checking whether the machine has VMware or not.
        """
        if not options:
            raise Exception, "Not enough options given to perform operation"
        opts = options.split('"')
        vmname = opts[1]
        if vmname.find('.vmx') == -1:
            raise Exception, "Options given does not have VMware Name in proper format."
        options = opts[0].split(' ')
        try:
            # check whether the machine is VMware
            result = self.__execCmd(options, [vmcmd, '-h'])
            if str(result).lower().find('no such file') != -1:
                raise Exception, "Could not run vmware-cmd command on host machine !!"
        except:
            raise Exception, "Could not run vmware-cmd command on host machine. Error Found:%s" % result
        try:
            # find path for the vm on host machine
            result = self.__execCmd(options, [vmcmd, '-l'])
            result = result.split('\n')
            bfound = False
            for res in result:
                if res.find(vmname) != -1:
                    bfound =  True
                    break
            if not bfound:
                raise Exception, "Could not find VM on host machine !!"
        except:
            raise Exception, "Could not find VM on host machine. Error Found:%s" % result
        try:
            # run the actual action
            if opmode == None:
                result = self.__execCmd(options, [vmcmd, res, command])
            else:
                result = self.__execCmd(options, [vmcmd, res, command, opmode])
        except:
            raise Exception, "Could not perform the action on VM. Error Found:%s" % result
        return result
    
    def __execCmd(self, options, cmd):
        """ This function is to run the command remotely.
        This will create a shell script run time that performs login and running command.
        Will also return the output after execution !!
        """
        hostname = options[0]
        loginname = ""
        passwd = ""
        if len(options) > 1:
            loginname = options[1]
        if len(options) > 2:
            passwd = options[2]
        output = ""
        try:
            output = scaremotecommand.scaRemoteCommand("%s@%s" %(loginname, hostname), cmd, passwd)
        except scaerror.ScaError, msg:
            if msg:
                output = msg
        return output
    
    # ----------------------------------------
    # Public functions
    # ----------------------------------------
    def powerStatus(self, node, options):
        """ This function is to get the power status of VM"""
        status = self.__runCmd(node, options, 'getstate')
        if status.find('off') != -1:
            status = kusu.power.STATUSOFF
        elif status.find('on') != -1:
            status = kusu.power.STATUSON
        else:
            status = kusu.power.STATUSNA
        return status

    def powerOff(self, node, options):
        """ This function is to power off VM"""
        result = self.powerStatus(node, options)
        if result == kusu.power.STATUSON:
            self.__runCmd(node, options, 'stop', 'hard')
        else:
            print "The Virtual Machine is already off !!"
        return kusu.power.SUCCESS

    def powerOn(self, node, options):
        """ This function is to power on VM"""
        result = self.powerStatus(node, options)
        if result == kusu.power.STATUSOFF:
            self.__runCmd(node, options, 'start', 'hard')
        else:
            print "The Virtual Machine is already on !!"
        return kusu.power.SUCCESS

    def powerCycle(self, node, options):
        """ This function is to power cycle VM"""
        result = self.powerStatus(node, options)
        if result == kusu.power.STATUSON:
            result = self.powerOff(node, options)
        self.powerOn(node, options)
        return kusu.power.SUCCESS

    def powerReset(self, node, options):
        """ This function is to reset the power of VM"""
        self.__runCmd(node, options, 'reset', 'hard')
        return kusu.power.SUCCESS

kusu.power.registerPlugin(vmpower)
