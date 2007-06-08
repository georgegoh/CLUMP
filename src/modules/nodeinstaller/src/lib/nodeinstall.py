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
from kusu.util.errors import EmptyNIISource
import urllib2
import kusu.util.log as kusulog
from xml.sax import make_parser, SAXParseException

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

    _niidict = {
    'source' : None,    # The NII source
    'name':'',          # Name of the node
    'installers':[],    # List of avaliable installers
    'repo':'',          # Repo location
    'ostype':'',        # OS type
    'installtype': '',  # Type of install to perform
    'nodegrpid':0 ,     # Node group ID
    'appglobal':{},     # Dictionary of all the appglobal data
    'nics':{},          # Dictionary of all the NIC info
    'partitions':{},    # Dictionary of all the Partition info.  Note key is only a counter
    'packages':[],      # List of packages to install
    'scripts':[],       # List of scripts to run
    'cfm': ''           # The CFM data
    }

    def __init__(self, niisource=None):
        super(NodeInstaller, self).__init__()
        self.source = niisource


    def __getattr__(self, name):
	""" Convenience method for accessing attributes. Code snippet
	    taken from autoinstall.installprofile. 
	"""
        
        if name in self._niidict.keys():
            return self._niidict[name]
        else:
            raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, name)

    def __setattr__(self, item, value):
    	""" Convenience method for setting attributes. Code snippet
    	    taken from autoinstall.installprofile. 
    	"""        
        if item in self._niidict.keys():
            self._niidict[item] = value
        else:
             raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, item)

    def parseNII(self):
        """ Parses the NII and places the resulting data into self.niidata """
        
        try:
            logger.debug('Parsing NII')
            logger.debug('niisource : %s' % self.source)
        
            if not self.source : raise EmptyNIISource
        
            niidata = NodeInstInfoHandler()
            p = make_parser()
            p.setContentHandler(niidata)
            p.parse(self.source)
            for i in ['name', 'installers', 'repo', 'ostype', 'installtype',
                'nodegrpid', 'appglobal', 'nics', 'partitions', 'packages',
                'scripts', 'cfm']:
                setattr(self,i,getattr(niidata,i))
                logger.debug('%s : %s' % (i,getattr(self,i)))
        except SAXParseException:
            logger.debug('Failed parsing NII!')
        except EmptyNIISource:
            logger.debug('NII Source is empty!')

        
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
        
    


