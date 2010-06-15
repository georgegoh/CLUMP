#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# 
# $Id$ 
# 

import os
import sys
import shutil
import atexit
from primitive.core.command import Command
from primitive.core.command import CommandFailException
from path import path
from you import YouUpdate
from rhn import RHNUpdate

class UpdateCommand(Command):

    def __init__(self, **kwargs):
        super(UpdateCommand, self).__init__(name='updatetool', 
                                            logged=True, 
                                            locked=True, 
                                            lockdir=os.getenv('PRIMITIVE_LOCKDIR', '/var/lock/subsys/primitive'))
        self.proxy = kwargs.get('proxy')

class YouUpdateCommand(UpdateCommand):

    def __init__(self, **kwargs):
        super(YouUpdateCommand, self).__init__(**kwargs)

        try:
            self.username = kwargs['username']
            self.password = kwargs['password']
            self.channel = kwargs['channel']
            self.arch = kwargs['arch']
            self.repopath = kwargs['repopath']

        except KeyError:
            raise CommandFailException,'required key not supplied'
 
    def execImpl(self):
        youu = YouUpdate(username = self.username, password = self.password,
                         channel = self.channel, 
                         arch = self.arch,
                         proxy = self.proxy)

        return youu.getUpdates(self.repopath)


class RHNUpdateCommand(UpdateCommand):

    def __init__(self, **kwargs):
        super(RHNUpdateCommand, self).__init__(**kwargs)

        try:
            self.username = kwargs['username']
            self.password = kwargs['password']
            self.serverid = kwargs['serverid']
            self.repopath = kwargs['repopath']
            self.arch = kwargs['arch']
            self.version = kwargs['version']

        except KeyError:
            raise CommandFailException,'required key not supplied'

        self.yumrhn = kwargs.get('yumrhn')
 
    def execImpl(self):
        rhn = RHNUpdate(username = self.username, password = self.password,
                        yumrhnURL = self.yumrhn,
                        serverid = self.serverid,
                        arch = self.arch,
                        version = self.version,
                        proxy = self.proxy)

        return rhn.getUpdates(self.repopath)
