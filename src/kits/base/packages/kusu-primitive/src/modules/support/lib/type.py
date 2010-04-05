#!/usr/bin/env python
# $Id: type.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
""" This module contains data types that are defined and used by primitive."""
class Struct(dict):
    """ An extended dictionary where you can define key/value pairs
        as easily as defining attributes in an object.

        > s = Struct(d1=1, d2='str')
        > s.d1
          1
        > s['d1']
          1
        > s.d2 = 'string'
        > s.d2
          'string'
        > s['d2']
          'string'
    """
    def __init__(self, dictionary=None, **kwargs):
        """Initialise with either a dictionary, or with key/value pairs."""
        if dictionary:
            self.update(dictionary)
        self.update(kwargs)

    def __getattr__(self, key):
        return dict.__getitem__(self, key)

    def __setattr__(self, key, value):
        self[key] = value

    def __repr__(self):
        return 'Struct(' + dict.__repr__(self) + ')'
