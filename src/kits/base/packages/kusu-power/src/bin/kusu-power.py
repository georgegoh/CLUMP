#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# $Id$
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
#   Author: sp
#   Date:   2006/06/24
#
# LAST CHANGED
#   $Author: $
#   $Date: $
#
# ---------------------------------------------------------------------------

"""
kusu-power command-line utility
"""

import sys
import logging
import warnings
from optparse import OptionParser
import time
import os
import os.path
import string

# Platform imports
import kusu.power
from kusu.util.lock import check_for_global_lock

DEFAULT_PLUGIN_PATH = None
DEFAULT_CONFIG_FILE = None

def buildPaths():
    """
    Create paths relative to installation
    """
    global DEFAULT_PLUGIN_PATH
    global DEFAULT_CONFIG_FILE

    powerModuleFile = os.path.abspath(kusu.power.__file__)
    powerModuleDirectory = os.path.dirname(powerModuleFile)
    DEFAULT_PLUGIN_PATH = (os.path.join(powerModuleDirectory, "powerplugins") + os.sep)

    confdir = os.path.join(powerModuleDirectory, "..")
    confdir = os.path.join(confdir, "..")
    confdir = os.path.join(confdir, "..")
    confdir = os.path.join(confdir, "etc")
    DEFAULT_CONFIG_FILE = os.path.join(confdir, "kusu-power.conf")


def doAction(nodename, action):
    """ Call the plugin actions """
    node = kusu.power.findNode(nodename)
    if not node:
        log.error("Node '%s' not found" % nodename)
        return kusu.power.FAILED

    try:
        if action == "powerstatus" or action == "status":
            result = node.powerStatus()
        elif action == "poweroff" or action == "off":
            result = node.powerOff()
        elif action == "poweron" or action == "on":
            result = node.powerOn()
        elif action == "powercycle" or action == "cycle":
            result = node.powerCycle()
        elif action == "powerreset" or action == "reset":
            result = node.powerReset()
        elif action == "uidstatus":
            result = node.uidStatus()
        elif action == "uidoff":
            result = node.uidOff()
        elif action == "uidon":
            result = node.uidOn()
        elif action == "info":
            #currently only available for IPMI
            result = node.getInfo()
        else:
            raise Exception, "Invalid action '%s'" % action
    except Exception, e:
        log.error("Error performing action : %s" % e)
        result = kusu.power.FAILED

    return result

class Parameters:
    """ Cmdline parameter parsing """
    def __init__(self):
        self.usage = "kusu-power [options] <nodelist> <on|off|cycle|reset|status>"
        parser = OptionParser(usage=self.usage)
        parser.add_option("-c", "--config_file", action="store", type="string",
                          dest= "conf_file", default=DEFAULT_CONFIG_FILE,
                          help="Define config-file")
        parser.add_option("-v", "--verbose", action="store_true", dest= "verbose", default=False,
			  help="Verbose run; display more information")
        parser.add_option("-d", "--debug", action="store_true", dest= "debug", default=False,
                          help="Debug run; display debug information")
        parser.add_option("-p", "--plugin_dir", action="store", type="string",
                          dest= "plugin_dir", default=DEFAULT_PLUGIN_PATH,
                          help="Define plugin directory)")
        parser.add_option("-r", "--retries", action="store", type="int",
                          dest= "retries", default=0,
                          help="Retry failed commands this many times before giving up.")
        parser.add_option("-i", "--interval", action="store", type="float",
                          dest= "interval", default=0,
                          help="Wait this many seconds between each node.")
        (self.opts, self.args) = parser.parse_args(sys.argv[1:])

def showwarning(message, category, filename, lineno):
    """
    showwarning function to replace the default function in the warnings module
    """
    log = logging.getLogger()
    log.warn("%s" % message)


def defaultLogging():
    """
    Set up logger
    """
    logging.getLogger("com.platform.power").setLevel(logging.ERROR)
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    if os.getenv("PmPowerLog") and hasattr(logging, os.getenv("PmPowerLog").upper()):
        log.setLevel(getattr(logging, os.getenv("PmPowerLog").upper()))
    stderr = logging.StreamHandler()
    stderr.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
    log.addHandler(stderr)
    warnings.showwarning = showwarning
    return log

def bracketExpand(arg):
    """
    Do bracket expand if available
    """
    try:
        import kusu.scaexpand
        return scaexpand.ScaExpand().scaBracketGroupExpand(arg)
    except ImportError:
        log.warn("module 'scaexpand' not available.. ignoring")
        return string.split(arg)

def main(params):
    """ Main cmdline function """
    failed = False

    if len(params.args) != 2:
        print params.usage
        sys.exit(1)

    nodelist = params.args[0]
    action = params.args[1]

    if params.opts.verbose:
        log.setLevel(logging.ERROR)
    if params.opts.debug:
        log.setLevel(logging.DEBUG)

    kusu.power.loadPlugins(log, params.opts.plugin_dir)
    kusu.power.readConfig(log, params.opts.conf_file)

    for arg in nodelist.split():
        for nodename in bracketExpand(arg):
            for _i in range(params.opts.retries + 1):
                result = doAction(nodename, action)
                if result == kusu.power.SUCCESS:
                    break
            print "%s: %s" % (nodename, result)
            if result != kusu.power.SUCCESS:
                failed = True
            if params.opts.interval:
                time.sleep(params.opts.interval)

    if failed:
        sys.exit(-1)

if __name__ == '__main__':
    check_for_global_lock()
    log = defaultLogging()
    log.setLevel(logging.FATAL)

    buildPaths()
    main(Parameters())


