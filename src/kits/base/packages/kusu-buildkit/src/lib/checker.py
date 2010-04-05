#!/usr/bin/env python
# $Id: checker.py 2110 2009-02-27 21:36:10Z ggoh $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This module handles syntax validation for the kitscript source.
"""

from kusu.util.errors import KitscriptValidateError

SUPPORTED_SRCTYPES = ['base', 'autotools', 'srpm', 'binary', 'distro', 'rpm', 'component', 'kit']

def getSyntaxValidator(obj):
    """ Factory function to return the correct Validator instance.
    """
    if not hasattr(obj,'srctype'): raise KitscriptValidateError
    if not obj.srctype in SUPPORTED_SRCTYPES: raise KitscriptValidateError
    _s = obj.srctype.capitalize() + 'Validator'
    _cls = eval(_s)
    return _cls(obj)


class BaseValidator(object):
    """ Base Validator class """

    def __init__(self, obj):
        self.base_attributes = ['name']
        self.attributes = []
        self.obj = obj
        
    def _add_attributes(self):
        for a in self.attributes:
            if not a in self.base_attributes:
                self.base_attributes.append(a)
        
    def validate(self):
        """ Validate the object. """
        
        self._add_attributes()
        li = [attribute for attribute in self.base_attributes \
            if hasattr(self.obj,attribute) and getattr(self.obj,attribute)]
        if sorted(li) <> sorted(self.base_attributes): return False
        
        return True
        
    def getMissingAttributes(self):
        """ Returns the list of missing attributes.
        """
        self._add_attributes()
        li = [attribute for attribute in self.base_attributes \
            if not hasattr(self.obj,attribute) or not getattr(self.obj,attribute)]
        return li        


class PackageProfileValidator(BaseValidator):
    """ This class validates PackageProfile objects. """

    def __init__(self, obj):
        super(PackageProfileValidator, self).__init__(obj)
        self.attributes = ['filename']
                
        
class AutotoolsValidator(PackageProfileValidator):

    def __init__(self, obj):
        super(AutotoolsValidator, self).__init__(obj)
        self.attributes = ['filename', 'installroot', 'version']


class SrpmValidator(PackageProfileValidator):

    def __init__(self, obj):
        super(SrpmValidator, self).__init__(obj)
        self.attributes = ['filename', 'version', 'release']

                
class BinaryValidator(PackageProfileValidator):

    def __init__(self, obj):
        super(BinaryValidator, self).__init__(obj)
        self.attributes = ['filename', 'installroot', 'version', 'release']

        
class RpmValidator(PackageProfileValidator):

    def __init__(self, obj):
        super(RpmValidator, self).__init__(obj)
        self.attributes = ['filename', 'version', 'release']


class DistroValidator(PackageProfileValidator):

    def __init__(self, obj):
        super(DistroValidator, self).__init__(obj)
        self.attributes = ['ostype']
    
class ComponentValidator(BaseValidator):
    """ This class validates KusuComponent objects. """
    
    def __init__(self, obj):
        super(ComponentValidator, self).__init__(obj)

        
class KitValidator(BaseValidator):
    """ This class validates KusuKit objects. """

    def __init__(self, obj):
        super(KitValidator, self).__init__(obj)        
