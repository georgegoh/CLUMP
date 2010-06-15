#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
""" This module contains exception classes used in the support module."""
from primitive.core.errors import ModuleException

# General Support exception - should be subclassed, and not
# used directly.
class SupportException(ModuleException): pass

# Util Exceptions hierarchy
class SupportUtilException(SupportException): pass
class DeviceNotFoundException(SupportUtilException): pass
class MountPointException(SupportUtilException): pass
class InvalidMacAddressException(SupportException): pass

class InvalidRPMHeaderException(SupportException): pass
class RPMComparisonException(SupportException): pass
class UnableToCalchecksumException(SupportException): pass

class repodataChecksumException(SupportException): pass
