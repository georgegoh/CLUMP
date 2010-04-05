
#!/usr/bin/env python
import atexit
import os
import shutil
import sys
from  primitive.configtool.plugins import BasePlugin
from  primitive.configtool.plugins import PluginException
from primitive.core.command import Command
from primitive.core.command import CommandFailException
from primitive.fetchtool.commands import FetchCommand
import Cheetah.Template
import tempfile
import StringIO
from path import path

from primitive.nodeinstall.nodeinstall import NodeInstaller
#from kusu.installer.util import remarkMBRs
#from kusu.boot.tool import getPartitionMap, makeDev
# from kusu.ui.text.screenfactory import * 
#from kusu.ui.text.navigator import Navigator
from primitive.system.hardware.nodes import checkAndMakeNode
from primitive.system.hardware import DiskProfile

class ImageCommand(Command):
    '''Base command class for all Imagetool commands'''
    def __init__(self,**kwargs):
        Command.__init__(self,**kwargs)
    

# Commands used by Node Installer
class NodeinstallerCommand(Command):
    def __init__(self,**kwargs):


        Command.__init__(self,**kwargs)
        self.nodeinst = NodeInstaller()
        
class RetrieveNIICommand(Command):
    '''Download and return required NII as an output string'''
    def __init__(self,**kwargs):
        if not kwargs['logged']:
            raise CommandFailException,"Logging must be enabled for this command!"
        Command.__init__(self,**kwargs)
        try:
            self.uri = kwargs['uri']
        except KeyError,e:
            raise CommandFailException("NII uri must be specified!")
        for key in ['logged', 'locked', 'logdir', 'lockdir']:
            if kwargs.has_key(key):
                self.__setattr__(key, kwargs[key])
            else:
                self.__setattr__(key, None)
        
    def execImpl(self):
        try:
            dest_dir = tempfile.mkdtemp('nodeinstall')
            try:
                self.logger.debug('Fetching %s' % self.uri)
                status,filename = FetchCommand(uri=self.uri,
                                               lockdir=self.lockdir,
                                               fetchdir=False,
                                               destdir=dest_dir,
                                               overwrite=True).execute()
                f = open(filename)
                data = f.read()
                self.logger.debug('Fetchtool data: %s' % data)
                f.close()
            finally:
                # ensure deletion of dest_dir if its created
                path(dest_dir).rmtree() 
            return StringIO.StringIO(data)
        except CommandFailException, e:
            msg = "nodeboot.cgi unavailable. " + \
                "Fetchcommand failed: %s" % (e)
            self.logger.error(msg)
            raise CommandFailException, msg
        except IOError, e:
            self.logger.error('%s', e)
            raise CommandFailException, str(e)
