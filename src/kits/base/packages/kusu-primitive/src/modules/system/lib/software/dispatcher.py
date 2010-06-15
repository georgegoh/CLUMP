#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
''' Dispatcher class
'''
from types import StringType
from primitive.system.software.dispatcher_dict import dispatcher_dict
from primitive.system.software.probe import OS
from primitive.core.errors import ModuleException
from primitive.support import osfamily

class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable


class Dispatcher:
    dict = None

    def get(key, default=None, os_tuple=OS()):
        try:
            (os, ver, arch) = os_tuple
        except ValueError:
            raise ModuleException, 'Dispatcher OS tuple %s is incomplete' % str(os_tuple)
        
        for item, value in zip(('os','ver','arch'), os_tuple):
            if type(value) != StringType:
                raise ModuleException, "Type '%s' of Dispatcher OS tuple item '%s' is non-string" % (type(value), item)
        
        try:
            dict = dispatcher_dict[key]
        except KeyError:
            return default

        try:
            # convert os_name to uppercase
            os_tuple = (os_tuple[0].upper(), os_tuple[1], os_tuple[2])
            return dict[os_tuple]
        except KeyError:
            return Dispatcher.fallback(dict, os_tuple, default)
    get = Callable(get)

    def keys():
        """ Returns the list of recognized keys that can be used with the get
            method.
        """
        os_tuple = OS()
        try:
            return dispatcher_dict.keys()
        except:
            return []
    keys = Callable(keys)

    def fallback(dict, (name, ver, arch), default):
        """ fallback is simply a last-ditch attempt to find a compatible
            dispatcher dictionary that can be used with the supplied
            OS,ver,arch.
        """
        fallback_os_tuple = None
        # rhel and sles also in fallback due to non-upper case letters case. eg: Rhel, rhel
        if name.lower() in osfamily.getOSNames('rhelfamily'):
            fallback_os_tuple = ('RHEL', ver.split('.')[0], arch)
        elif name.lower() in ['sles', 'opensuse']:
            fallback_os_tuple = ('SLES', ver.split('.')[0], arch)
        else:
            fallback_os_tuple = (name, ver.split('.')[0], arch)

        try:
            return dict[fallback_os_tuple]
        except KeyError:
            return default
    fallback = Callable(fallback)


if __name__ == "__main__":
    print Dispatcher.get('webserver_usergroup')
    print Dispatcher.get('nosuchkey')
    print Dispatcher.get('nosuchkey', default='Some default value')

    # The following should print '/Server/'.
    # This is to test:
    # 1. we have converted the os_name to uppercase.
    # 2. passing in an os_tuple.
    print Dispatcher.get('yum_repo_subdir', os_tuple=('rhel', '5', 'x86_64'))
