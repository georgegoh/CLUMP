#!/usr/bin/env python
# $Id$
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See COPYING file for details.
#

try:
    import subprocess
except:
    from popen5 import subprocess

import os
import sys
import signal


def responsive_run(args):
    '''Custom wrapper function for subprocess.Popen to return output and error strings.

       subprocess.call prints to stdout and stderr as and when there is anything to print.
       Such responsiveness is needed in kusu-kit-install. However, it does not return the
       compiled output and error strings, which is also needed. So, this function is used
       as a replacement.'''

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Interrupt should kill both kusu-kit-install and any subprocess
    def kill(blah1, blah2):
        try:
            os.kill(p.pid, 9)
        except OSError:
            pass
    old_handler = signal.signal(signal.SIGINT, kill)

    # Poll for output and print
    out = []
    while True:
        o = p.stdout.readline()
        if o == '' and p.poll() != None:
            break

        out.append(o)
        sys.stdout.write(o)
        sys.stdout.flush()

    # Return compiled output and error string with the return code
    outstr = ''.join(out)
    errstr = p.stderr.read()
    sys.stderr.write(errstr)
    sys.stderr.flush()

    signal.signal(signal.SIGINT, old_handler)
    return outstr, errstr, p.returncode


def exit_with_msg(msg='Error: Please check usage', exitcode=1):
    '''Helper function to write to error stream and exit with the return code.
    '''

    if msg and not msg.endswith('\n'):
        msg += '\n'

    sys.stderr.write(msg)

    sys.exit(exitcode)

