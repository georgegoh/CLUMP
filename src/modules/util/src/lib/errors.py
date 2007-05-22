#!/usr/bin/env python
# $Id$
#
# Kusu Exceptions.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
import exceptions


# General
class KusuError(exceptions.Exception): pass
class InvalidPathError(KusuError): pass
class UnknownTypeError(KusuError): pass
class FileDoesNotExistError(KusuError): pass
class CommandFailedToRun(KusuError): pass

# partitiontool
class NoDisksFoundError(KusuError) : pass
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
class MountFailedError(KusuError): pass
class VolumeGroupHasBeenDeletedError(KusuError): pass

# util
class CopyFailedError(KusuError): pass

# util/distro
class LoadDistroConfFailedError(KusuError): pass
class HTTPError(KusuError): pass
class FTPError(KusuError): pass

# networktool
class InterfaceNotBroughtUpError(KusuError): pass
class InterfaceNotBroughtDownError(KusuError): pass
class FailedDHCPRequestError(KusuError): pass
class FailedSetStaticIPError(KusuError): pass
class NotSupportedOperatingSystem(KusuError): pass
class InterfaceNotFound(KusuError): pass


