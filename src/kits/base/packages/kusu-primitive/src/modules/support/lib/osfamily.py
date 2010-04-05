#!/usr/bin/env python
# $Id: osfamily.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
'''Methods to utilize OS names in the OS Family dictionary.
'''

from primitive.support.osfamily_dict import osfamily_dict

def getOSNames(key, default=[]):
    """ Returns the list of os tuples belonging to the specified os family key.
    """
    try:
        return osfamily_dict[key]
    except KeyError:
        return default

def keys():
    """ Returns the list of recognized keys that can be used with the getOSNames method.
    """
    try:
        return osfamily_dict.keys()
    except:
        return []

def matchTuple(repo_os, os_tuples):
    """ Returns True if repo_os matches anything in os_tuples. Otherwise returns False.
        os_tuples must be a list of and repo_os must a single tuple of the form
        (os name, major version, minor version, architecture).
    """
    for tuple in os_tuples:
        if tuple[3] == 'noarch':
            tuple = tuple[:3]+('*',) # for arch element, 'noarch' = '*'
        for i in range(4):
            if repo_os[i] != tuple[i] and '*' != tuple[i]:
                break # no match here
        else: # looped without breaking, so match found
            return True
    return False # repo os does not match any tuple

if __name__ == "__main__":
    print getOSNames('rhelfamily')
