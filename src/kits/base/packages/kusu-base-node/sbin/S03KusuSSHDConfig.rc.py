#!/usr/bin/env python
# $Id
#
# Copyright 2009 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import rcplugin
import os
import string
import tempfile

from path import path

class KusuRC(rcplugin.Plugin):

    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name    = 'sshdconfig'
        self.desc    = 'config sshd for SLES10'
        self.ngtypes = ['installer', 'compute', 'compute-imaged', 'compute-diskless']
        self.delete  = False
        # this should be moved to primitive?
        self.sshdconfig = '/etc/ssh/sshd_config'
        self.sshdservice = 'sshd'

    def run(self):
        
        if not os.path.exists(self.sshdconfig):
            return False
        fp = open(self.sshdconfig, 'r')
        lines = fp.readlines()
        fp.close()

        lineno = 0
        for line in lines:
            lineno += 1
            # ignore space lines
            if line.isspace():
                continue

            linestrip = string.strip(line)
            # comments
            if linestrip[0] == "#":
                continue
            try:
                key,val = string.split(linestrip, ' ', 1)
            except:
                continue

            # open password authentication.
            if key == 'PasswordAuthentication' and val == 'no':
                line = 'PasswordAuthentication yes\n'
                lines[lineno-1] = line
        
        # replace config file for sshd
        # CREATE temp file and update the config file.
        tmpfd, tmppath = tempfile.mkstemp(suffix='.txt', text=True)
        try:
            os.close(tmpfd)
        except:
            os.unlink(tmppath)
            return False

        tmpfp = open(tmppath, 'w')
        try:
            tmpfp.writelines(lines)
        except:
            tmpfp.close()
            return False
        tmpfp.close()

        # Back up old sshd config file.
        backupfile = self.sshdconfig + '.bk'
        os.rename(self.sshdconfig, backupfile)

        # Create new sshd config file.
        os.rename(tmppath, self.sshdconfig)
        
        # Restart sshd if it is running.
        success, (retcode, out, err) = self.service(self.sshdservice, 'status')
        if retcode.find('running'):
            success, (retcode, out, err) = self.service(self.sshdservice, 'restart')
        return True

