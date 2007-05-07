#!/usr/bin/env python
# $Id$
#
# Kusu Partition Tool Exceptions.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
import exceptions

class KusuError(exceptions.Exception): pass
class OutOfSpaceError(KusuError): pass
class DuplicateNameError(KusuError): pass
class DuplicateMountpointError(KusuError): pass
class NameNotFoundError(KusuError): pass
class UnknownPartitionTypeError(KusuError): pass
class PartitionSizeTooLargeError(KusuError): pass
class PartitionIsPartOfVolumeGroupError(KusuError): pass
class VolumeGroupMustHaveAtLeastOnePhysicalVolumeError(KusuError): pass
class PhysicalVolumeAlreadyInLogicalGroupError(KusuError): pass
class CannotDeletePhysicalVolumeFromLogicalGroupError(KusuError): pass
class InsufficientFreeSpaceInVolumeGroupError(KusuError): pass
class LogicalVolumeAlreadyInLogicalGroupError(KusuError): pass
class CannotDeleteLogicalVolumeFromLogicalGroupError(KusuError): pass
class NotPhysicalVolumeError(KusuError): pass
class InvalidVolumeGroupExtentSizeError(KusuError): pass
class PhysicalVolumeStillInUseError(KusuError): pass
class LogicalVolumeStillInUseError(KusuError): pass
