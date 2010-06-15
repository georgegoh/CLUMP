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

import os
import imp
import glob

_plugin_classes = []
_devices = []
_nodes = []

STATUSON = "ON"
STATUSOFF = "OFF"
STATUSNA = "N/A"

FAILED = "FAILED"
SUCCESS = "SUCCESS"


class Device:
    """Class to hold power devices, which use a certain 'plugin'"""
    def __init__(self, log, name, plugin, options):
        self.log = log
        self.__name__ = name
        self.plugin = self._instanciatePlugin(log, name, plugin, options)
        return

    def _instanciatePlugin(self, log, name, plugin, options):
        global _plugin_classes
        
        for plugin_class in _plugin_classes:
            if plugin_class.__name__ == plugin:
                try:
                    log.debug("Instanciating %s plugin" % plugin_class.__name__)
                    instance = plugin_class(log, name, options)
                except Exception, e:
                    log.error("Unable to instanciate plugin: %s:" % plugin_class.__name__)
                    log.error(e)
                else:
                    return instance
        raise Exception, "Plugin '%s' not found" % plugin


class Node:
    """Class to hold each node in the configuration"""
    def __init__(self, log, name, device, options):
        self.log = log
        self.__name__ = name
        self.device = self._instanciateDevice(log, device)
        self.options = options
        return

    def _instanciateDevice(self, log, device):
        global _devices
        
        for dev in _devices:
            if dev.__name__ == device:
                return dev
        raise Exception, "Device '%s' not found" % device
        
    def powerStatus(self):
        return self.device.plugin.powerStatus(self.__name__, self.options)
    
    def powerOff(self):
        return self.device.plugin.powerOff(self.__name__, self.options)

    def powerOn(self):
        return self.device.plugin.powerOn(self.__name__, self.options)

    def powerCycle(self):
        return self.device.plugin.powerCycle(self.__name__, self.options)

    def powerReset(self):
        return self.device.plugin.powerReset(self.__name__, self.options)

    def uidStatus(self):
        return self.device.plugin.uidStatus(self.__name__, self.options)

    def uidOff(self):
        return self.device.plugin.uidOff(self.__name__, self.options)

    def uidOn(self):
        return self.device.plugin.uidOn(self.__name__, self.options)


class Plugin:
    """Super-class for plugins that "power" configures"""
    def __init__(self, log, name, options):
        self.log = log
        self.__name__ = name
        self.options = options.split()

    def powerStatus(self, node, options):
        return STATUSNA

    def powerOff(self, node, options):
        return FAILED

    def powerOn(self, node, options):
        return FAILED

    def powerCycle(self, node, options):
        return FAILED
        
    def powerReset(self, node, options):
        return FAILED
        
    def uidStatus(self, node, options):
        return STATUSNA

    def uidOff(self, node, options):
        return FAILED

    def uidOn(self, node, options):
        return FAILED


def registerPlugin(plugin_class):
    """Callback for plugins to register themselves with the framework"""
    global _plugin_classes

    _plugin_classes.append(plugin_class)


def _loadPlugin(log, plugin, plugin_path):
    """Internal function to load a specific plugin from a specific path"""
    log.debug("Loading %s from %s" % (plugin, plugin_path))
    try:
        modulename = os.path.splitext(os.path.basename(plugin))[0]
        (fp, pathname, description) = imp.find_module(modulename, [plugin_path])
        try:
            module = imp.load_module(modulename, fp, pathname, description)
        finally:
            # Since we may exit via an exception, close fp explicitly.
            if fp:
                fp.close()
        log.debug('Plugin loaded: %s' % modulename)
    except Exception, e:
        log.error("Unable to load plugin from: %s" % plugin)
        log.error(e)


def loadPlugins(log, plugin_path):
    """Load all available plugins in a specific directory"""
    for plugin in glob.glob('%s/*.py' % plugin_path):
        _loadPlugin(log, plugin, plugin_path)


def readConfig(log, fname):
    """Read configuration and populate devices and nodes"""
    global _devices
    global _nodes
    
    try:
        f = file(fname)
        lines = f.readlines()
        f.close()
    except Exception, e:
        log.error("Unable to load global config : %s" % e)
        return
    
    linenumber = 1
    for line in lines:
        # Strip comments
        line = line.split('#')[0]
        if not line:
            linenumber = linenumber + 1
            continue
        fields = line.split()
        if not fields:
            linenumber = linenumber + 1
            continue

        try:
            keyw = fields[0]
            name = fields[1]
            ext = fields[2]
            options = options = " ".join(fields[3:])
        except:
            log.error("Format error on line #%d in %s" % (linenumber, fname))
            linenumber = linenumber + 1
            continue
        
        if keyw == "device":
            try:
                device = Device(log, name, ext, options)
            except Exception, e:
                log.error("Error creating device '%s' : %s" % (name, e))
            else:
                _devices.append(device)
                log.debug("Added device '%s'" % name)
        elif keyw == "node":
            try:
                node = Node(log, name, ext, options)
            except Exception, e:
                log.error("Error creating node '%s' : %s" % (name, e))
            else:
                _nodes.append(node)
                log.debug("Added node '%s'" % name)
        else:
            log.warn("Unrecognized keyword '%s' on line #%d in %s" % (keyw, linenumber, fname))

        linenumber = linenumber + 1


def findNode(nodename):
    """Find a specific node"""
    global _nodes
    
    for n in _nodes:
        if n.__name__ == nodename:
            return n
    return None
