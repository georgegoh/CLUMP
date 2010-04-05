#!/usr/bin/python
#-*- coding: utf-8 -*-
#
# $Id: powercmd.py 3126 2009-10-20 07:29:26Z abuck $
#
# Module --------------------------------------------------------------------
#
# $RCSfile$
#
# COPYRIGHT NOTICE
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See COPYING for details.
#
# CREATED
#   Author: rk
#   Date:   2003/11/14
#
# LAST CHANGED
#   $Author: kbjornst $
#   $Date: 2008-11-25 06:07:03 -0500 (Tue, 25 Nov 2008) $
#
# ---------------------------------------------------------------------------

"""
Module for running external commands
"""

import os
import sys
import types
import kusu.powertempfile
import logging

class PmCommandFailed(Exception):
    """
    Exception used for failing commands
    """
    def __init__(self, command, ret, output, error):
        """
        PmCommandFailed(command, ret, output, error) -> PmCommandFailed object

        command -- the command that failed
        ret -- the exit code from the shell wrapper
        output -- the output from the command
        error -- the output to stderr from the command
        
        Exception to represent failed PmCommands
        """
        Exception.__init__(self, "command failed: %s" % command)
        self.command = command
        self.ret = ret
        self.output = output
        self.error = error

    def __str__(self):
        """
        Return string representation of exception object
        """
        return "'%s' failed with shell exit code %d\n%s\n%s" % (self.command, 
                self.ret, self.error, self.output)


def __getfd(filespec, readOnly = 0):
    if type(filespec) == types.IntType:
        return filespec
    if filespec == None:
        filespec = "/dev/null"
                
    flags = os.O_RDWR | os.O_CREAT
    if (readOnly):
        flags = os.O_RDONLY
    return os.open(filespec, flags)

def pmsystem(command, stdin = 0, stdout = 1, stderr = 2):

    # ignore signals in parent
    # XXX: Apparently this doesn't work if the program
    # is multithreaded.
    #intr = signal.getsignal(signal.SIGINT)
    #quit = signal.getsignal(signal.SIGQUIT)
    #signal.signal(signal.SIGINT, signal.SIG_IGN)
    #signal.signal(signal.SIGQUIT, signal.SIG_IGN)
    
    childpid = os.fork()
    if childpid == 0:
        stdin = __getfd(stdin)
        if stdout == stderr:
            stdout = __getfd(stdout)
            stderr = stdout
        else:
            stdout = __getfd(stdout)
            stderr = __getfd(stderr)

        if stdin != 0:
            os.dup2(stdin, 0)
            os.close(stdin)
        if stdout != 1:
            os.dup2(stdout, 1)
            if stdout != stderr:
                os.close(stdout)
        if stderr != 2:
            os.dup2(stderr, 2)
            os.close(stderr)
                
        for i in range(3, 1024):
            try:
                os.close(i)
            except OSError:
                pass
 
        #signal.signal(signal.SIGINT, intr)
        #signal.signal(signal.SIGQUIT, quit)
           
        try:
            os.execvp("/bin/sh", ["sh", "-c", command])
        finally:
            sys.exit(1)

    status = -1
    status = os.waitpid(childpid, 0)[1]

    #signal.signal(signal.SIGINT, intr)
    #signal.signal(signal.SIGQUIT, quit)

    return status
        

class PmCommand:
    """
    Class representing the execution of an external command
    """
    def __init__(self, command, check_stderr=0):
        """
        PmCommand(command[, check_stderr]) -> PmCommand object

        command -- the command to be executed
        check_stderr -- raise exception if the command outputs data to stderr

        The command is run with system() - shell expansion will occur
        """
        self.log = logging.getLogger("com.platform.power")
        self.log.info("%s", command)
        out = kusu.powertempfile.NamedTemporaryFile()
        err = kusu.powertempfile.NamedTemporaryFile()

        # Can't use os.system() it doesn't close filedescriptors and child
        # processes will thus inherit our fildescriptors (which isn't desired).
        #ret = os.system("( %s ) > %s 2> %s < /dev/null" % \
        #      (command, out.name, err.name))
        ret = pmsystem(command, "/dev/null", out.name, err.name)
        err_data = err.read()
        out_data = out.read()
        err.seek(0)
        out.seek(0)
        if ret or (check_stderr and err_data):
            self.log.warn("Command failed with exit-code %d", ret)
            self.log.warn(err_data)
            self.log.warn(out_data)
            raise PmCommandFailed(command, ret, out_data, err_data)
        self.log.debug(err_data)
        self.log.debug(out_data)
        self.out = out

    def read(self, *args):
        """
        read() -> string

        *args -- standard optional arguments for read.

        Read data from the command's stdout
        """
        data = self.out.read(*args)
        return data

    def readlines(self):
        """
        readlines() -> list of string

        Read multiple lines from the command
        """
        return self.out.readlines()
