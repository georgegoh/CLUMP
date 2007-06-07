#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
import os
from kusu.autoinstall.scriptfactory import KickstartFactory
from kusu.autoinstall.autoinstall import Script
from kusu.autoinstall.installprofile import Kickstart
from kusu.partitiontool import partitiontool
from kusu.nodeinstaller import NodeInstInfoHandler
import urllib2
import kusu.util.log as kusulog
from xml.sax import make_parser

logger = kusulog.getKusuLog('nodeinstaller.NodeInstaller')
logger.addFileHandler()

def retrieveNII(niihost, node):
    """ Downloads the NII from the niihost.
        FIXME: currently a hardcoded url!!
    """
    url = 'http://%s/mirror/fc6/i386/os/nii.xml' % niihost
    try:
        logger.debug('Fetching %s' % url)
        f = urllib2.urlopen(url)
        logger.debug('urlopen returned object: %r' % f)
        data = f.read()
        logger.debug('urlopen data: %s' % data)
        return data
    except urllib2.HTTPError, e:
        logger.debug(str(e))
        return None

class NodeInstaller(object):
    """ The model for nodeinstaller. This class provides access to
        the data and methods to perform the operations for automatic
        node provisioning. 
    """

    def __init__(self, niisource=None):
        super(NodeInstaller, self).__init__()
        self.niisource = niisource
        self.niidata = NodeInstInfoHandler()

    def parseNII(self):
        """ Parses the NII and places the resulting data into self.niidata """
        logger.debug('Parsing NII')
        logger.debug('niisource : %s' % self.niisource)
        p = make_parser()
        p.setContentHandler(self.niidata)
        p.parse(self.niisource)
        for i in ['name', 'installers', 'repo', 'ostype', 'installtype',
            'nodegrpid', 'appglobal', 'nics', 'partitions', 'packages',
            'scripts', 'cfm']:
            logger.debug('%s : %s' % (i,getattr(self.niidata,i)))
        
    def setupNetworking(self):
        """ Sets the networking settings for the distro-specific auto configuration later. """
        pass
        
    def adaptNIIPartitionSchema(self):
	""" Adapts the partition schema provided by the NII into
	    something thats more amenable to partitiontool's schema.
	"""
        pass
        
    def setupPartitioning(self):
        """ Set the automatic partitioning. """
        # trash the current disk and start afresh
        diskprofile = partitiontool.DiskProfile(fresh=True)
        # get the default schema
        schema = self.adaptNIIPartitionSchema()
        
        
    def setupAutoInstall(self):
        pass
        
    


