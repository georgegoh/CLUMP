#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import sys
from optparse import OptionParser
import sqlalchemy as sa
try:
    import subprocess
except ImportError:
    from popen5 import subprocess

from kusu.uat import UATPluginBase, UATHelper

usage = """usage: check_nics [options] remote_host"""
SSH_COMMAND = '/usr/bin/ssh'
SSH_FAILURE_EXIT_STATUS = 255
DEFAULT_SSH_CONNECT_TIMEOUT_SECONDS = '10'

# The desired result is a command as follows:
# $ ssh compute-00-00 -o ConnectTimeout=10 -o PasswordAuthentication=no -o PubkeyAuthentication=yes ifconfig | grep 
# ConnectTimeout: we don't want to wait the default TCP timeout (3 minutes?)
#                 should the remote host be unreachable
# PasswordAuthentication: we disable password authentication as we won't be
#                         redirecting any input and we don't want the process
#                         to hang
# PubkeyAuthentication: we make sure that public key authentication is enabled
#                       for this connection
SSH_COMMAND_OPTIONS = ['-o', 'ConnectTimeout=10', '-o', 'PasswordAuthentication=no', '-o', 'PubkeyAuthentication=yes']
IFCONFIG_COMMAND = ['ifconfig ']
GREP_COMMAND = ['grep -P ']
ROUTE_COMMAND = ['route -n ']


class CheckNICS(UATPluginBase):

    def __init__(self, args=None):
        super(CheckNICS, self).__init__()
        self._logger = args['logger']
        self._db = args['db'] 
        self._host = None
       
        self._cmd_returncode = 0
       
    def pre_check(self):
        pass

    def post_check(self):
        pass

    def node_setup(self, node):
        pass

    def node_teardown(self, node):
        pass

    def run(self, args):
        nii_config = {} 
        self._interface_list = []
        self._cmd_out = ''  
        self._cmd_err = ''
  
        parser = self._configure_options()
        options, remaining_args = parser.parse_args(args[1:])
           
        if len(remaining_args) != 1:  # require only one host
            parser.pring_usage(file = sys.stderr)
            self._status = 'Please provide a host\n'
            self._logger.info('Please provide a host\n')
            return 1, self._status

        self._host = remaining_args[0]
        if options.interface is not None:
            if not self._device_exists(option.interface, self._host):
                self._status = 'Interface %s is not configured on host %s ' % (options.interface, self._host)
                return 1, self._status 
            self._interface_list.append(options.interface)
        else:
            self._get_all_interface_for_node()

        for interface in self._interface_list:
            nii_config = self._get_network_config_info(interface)
            returncode = self._check_nic_configuration(nii_config, interface)
            if returncode:
                return returncode, self._status

            if nii_config['type'] == 'public':
                returncode = self._check_gateway(nii_config['gateway'], interface)
                if returncode:
                    return returncode, self._status  

        returncode = 0
        self._status = "Nics configuration check passed for all interfaces."
        return returncode, self._status

    def _configure_options(self):
        """Sets up command line options"""

        parser = OptionParser(usage=usage)
        parser.add_option('-i', '--interface',
                          help='Specify the device to test. \
                          If not specified we test all the available interfaces on the host.')
        return parser

    def _get_all_interface_for_node(self):
        stmt = sa.select([self._db.Networks.c.device],
                              whereclause=sa.and_(self._db.Nodes.c.name==self._host,
                                                  self._db.Nodes.c.nid==self._db.Nics.c.nid,
                                                  self._db.Nics.c.netid==self._db.Networks.c.netid))  

        results = stmt.execute().fetchall()
        for record in results:
            self._interface_list.append(record['device'])


    def _check_nic_configuration(self, nii_config, interface):
        ifconfig_cmd = IFCONFIG_COMMAND + [interface]
        cmd = [SSH_COMMAND, self._host] + SSH_COMMAND_OPTIONS + ifconfig_cmd
        sshP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = sshP.communicate()
        # Assume ssh pass as the dependend check check_ssh is performed first.
        self._cmd_out += out
        self._cmd_err += err
        if not out:
            self._status = err
            return 1
         
        if str(nii_config['usingdhcp']) != 'f':
            return 0
        for key, value in nii_config.iteritems():
            if key in ['usingdhcp', 'type', 'gateway']:
                continue
                
            if key == 'mac':
                value.upper()

            if out.find(value) < 0:
                self._status = "Wrong \'%s\' for interface \'%s\'" % (key, interface)
                return 1 
                
        return 0

    def _get_network_config_info(self, interface):
        stmt = sa.select([self._db.Networks.c.subnet, self._db.Networks.c.gateway, self._db.Networks.c.type,
                          self._db.Networks.c.usingdhcp, self._db.Nics.c.mac, self._db.Nics.c.ip],
                         whereclause=sa.and_(self._db.Nodes.c.name==self._host,
                                             self._db.Nodes.c.nid==self._db.Nics.c.nid,
                                             self._db.Nics.c.netid==self._db.Networks.c.netid,
                                             self._db.Networks.c.device==interface))
        return stmt.execute().fetchone()

    def _check_gateway(self, gateway, interface):
        grep_cmd = GREP_COMMAND + ['\'^0.0.0.0\s*%s\'' % gateway] 
        cmd = [SSH_COMMAND, self._host] + SSH_COMMAND_OPTIONS + ROUTE_COMMAND  + ['|'] + grep_cmd 
        sshP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = sshP.communicate()
        self._cmd_out += out
        self._cmd_err += err
        if not out or out.split()[-1] != interface:
            self._status = "The default gateway \'%s\' for interface \'%s\' is not setup properly." % (gateway, interface)
            return 1

        return 0 

    def generate_output_artifacts(self, artifact_dir):
        if self._cmd_out:
            filename = artifact_dir / self._host / 'check_nics.out'
            UATHelper.generate_file_from_lines(filename, [self._status + '\n'] + [self._cmd_out])
        if self._cmd_err:
            filename = artifact_dir / self._host / 'check_nics.err'
            UATHelper.generate_file_from_lines(filename, [self._status + '\n'] + [self._cmd_err])
