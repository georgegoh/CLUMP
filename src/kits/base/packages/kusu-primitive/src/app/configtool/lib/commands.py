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
from path import path


class ConfigCommand(Command):
    ''' The Config Command takes a plugin , a template and arguments to it.
    It initialises the plugin. Calling execute will result in the result string
    being returned to the caller.'''
    def __init__(self,**kwargs):
        ''' The configtool initialisation takes a cheetah plugin and saves it
        locally. It then initialises the plugin with this file and sets a
        callback to remove it when done.'''
        Command.__init__(self,**kwargs)
        #Ensure we cannot be locked -- XXX comment it out till we can figure out
        # correct way to propagate locking directories
#         if self.locked:
#             raise CommandFailException, 'Config Tool cannot be locked'
        # Note however that a lockdir is needed to pass into fetchtool. if required.
        #Check for Config Tool Framework specific commands
        try:
            self.plugin_ref = kwargs['plugin']
            self.plugin_template_uri = kwargs['template']
            self.plugin_args = kwargs['plugin_args']
        except KeyError,e:
            raise CommandFailException,\
                'Required arguments not provided to configtool : %s' % e
        #Perform basic validation on the supplied plugin
        try:
            if not issubclass(self.plugin_ref,BasePlugin):
                raise CommandFailException,\
                    'A valid plugin has not been supplied to ConfigTool'
        except TypeError,e:
            raise CommandFailException,\
                'Plugin provided is not a valid class! %s' % e
        #Try to obtain the template from the URI
        try:
            dest_dir = tempfile.mkdtemp('configtool')
            if hasattr(self,'lockdir'):
                status,tmpl = FetchCommand(uri=self.plugin_template_uri,
                                           fetchdir=False,
                                           destdir=dest_dir,
                                           lockdir = self.lockdir,
                                           overwrite=True).execute()
            else:
                status,tmpl = FetchCommand(uri=self.plugin_template_uri,
                                           fetchdir=False,
                                           destdir=dest_dir,
                                           overwrite=True).execute()
            #delete destdir
            self.registerPostCallback(lambda : path(dest_dir).rmtree())
        except CommandFailException,e:
            path(dest_dir).rmtree(ignore_errors=True) # clean up destdir
            raise CommandFailException,\
                'Failed obtaining template for plugin %s' % e
        if not tmpl.exists() or not tmpl.isfile():
            path(dest_dir).rmtree(ignore_errors=True) #clean up destdir
            raise CommandFailException,'Failed opening template file'
        #The template is good, save it
        self.template = tmpl
        try:
            self.plugin = self.plugin_ref(self.template, self.plugin_args)
        except TypeError,e:
            path(dest_dir).rmtree(ignore_errors=True) #clean up destdir
            raise CommandFailException,\
                'Reference to provided plugin not callable %s' % e
        except NotImplementedError,e:
            path(dest_dir).rmtree(ignore_errors=True) #clean up destdir 
            raise NotImplementedError,e # failure but 
        except PluginException,e :
            path(dest_dir).rmtree(ignore_errors=True) #clean up destdir
            raise CommandFailException,\
                'Error initialising config plugin'

    def execImpl(self):
        ''' Call the initialised plugin and return result'''
        return  self.plugin.run()
        
