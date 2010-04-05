#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# 
# $Id$ 
# 
# Copyright (C) 2010 Platform Computing Inc. 
# 

''' FetchTool is a primitive app used to fetch a file or directory from a URI.
    This module is intended to be UBI-15 compliant.
'''
import urlparse
from path import path
from primitive.fetchtool.helper import isDestWritable
from primitive.fetchtool.helper import checkForRequiredArgs
from primitive.fetchtool.fetchhandler import FileFetchHandler
from primitive.fetchtool.fetchhandler import HTTPFetchHandler
from primitive.fetchtool.fetchhandler import HTTPSFetchHandler
from primitive.fetchtool.fetchhandler import YOUFetchHandler
from primitive.fetchtool.fetchhandler import RHNFetchHandler
from primitive.core.command import Command, CommandFailException
from primitive.core.errors import CommandMissingArgsException
from primitive.core.errors import ExistingDestCannotBeOverwrittenException

# urlparse by default does not recognise
# these protocols, so we add them.
for scheme in ('rhn', 'rhns', 'you', 'scp'):
    urlparse.uses_netloc.insert(0, scheme)
    urlparse.uses_query.insert(0, scheme)

class URICommand(Command):
    def __init__(self, **kwargs):
        super(URICommand, self).__init__(**kwargs)
        self.kwargs = kwargs


class FetchCommand(URICommand):
    ''' Command to fetch a URI.'''
    PROTOCOL_HANDLER_DICT = { 'file': FileFetchHandler,
                              'http': HTTPFetchHandler,
                              'https': HTTPSFetchHandler,
                              'rhn': RHNFetchHandler,
                              'you': YOUFetchHandler }

    def __init__(self, **kwargs):
        super(FetchCommand, self).__init__(name='fetchtool', logged=True,
                                  locked=False, **kwargs)
        self.protocol_fetchhandler = self._getProtocolHandler(kwargs['uri'])()
        self.required_args = ['uri', 'fetchdir', 'destdir', 'overwrite']
        self.required_args.extend(self.protocol_fetchhandler.required_args)
        valid, missing = checkForRequiredArgs(self.kwargs, self.required_args)
        if not valid:
            raise CommandMissingArgsException, \
                  'Fetching %s requires the following missing arguments: %s' % \
                  (self.kwargs['uri'], missing)
        self.registerPreCallback(self.checkDestOptions)

    def _getProtocolHandler(self, uri):
        protocol = urlparse.urlparse(uri)[0]
        try:
            handler = self.PROTOCOL_HANDLER_DICT[protocol]
        except KeyError:
            raise CommandFailException, \
                  'The protocol %s is not supported' % protocol
        return handler

    def checkDestOptions(self):
        ''' If destination exists, make sure it can be overwritten,
            otherwise, raise ExistingDestCannotBeOverwrittenException.
        '''
        # Check file destinations only.
        if not self.kwargs['fetchdir']:
            src = urlparse.urlparse(self.kwargs['uri'])[2]
            dest = path(self.kwargs['destdir']) / \
                   path(self.kwargs['uri']).basename()
            if not isDestWritable(dest,
                                  self.kwargs['fetchdir'],
                                  self.kwargs['overwrite']):
                raise ExistingDestCannotBeOverwrittenException, \
                      'Cannot overwrite existing destination.'
            # remove destination if it exists(unless the caller specifies
            # them to be the same.
            elif dest.exists() and src!= dest:
                dest.remove()

    def execImpl(self):
        ''' Dispatch the fetching to the appropriate fetchhandler
            for the protocol.
        '''
        return self.protocol_fetchhandler.fetch(**self.kwargs)
