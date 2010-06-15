#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#

# General
class SystemException(Exception): pass
class PartitionException(SystemException): pass

# partitiontool
class PartitionSchemaError(PartitionException): pass
class DiskProfileNotEmptyError(PartitionException): pass
class NoDisksFoundError(PartitionException) : pass
class OutOfSpaceError(PartitionException): pass
class DuplicateNameError(PartitionException): pass
class DuplicateMountpointError(PartitionException): pass
class NameNotFoundError(PartitionException): pass
class UnknownPartitionTypeError(PartitionException): pass
class PartitionSizeTooLargeError(PartitionException): pass
class CannotDeleteExtendedPartitionError(PartitionException): pass
class MountpointAlreadyUsedError(PartitionException): pass
class CannotLabelPartitionError(PartitionException): pass

# partitiontool - LVM errors
class PartitionIsPartOfVolumeGroupError(PartitionException): pass
class VolumeGroupMustHaveAtLeastOnePhysicalVolumeError(PartitionException): pass
class PhysicalVolumeAlreadyInLogicalGroupError(PartitionException): pass
class CannotDeletePhysicalVolumeFromLogicalGroupError(PartitionException): pass
class InsufficientFreeSpaceInVolumeGroupError(PartitionException): pass
class LogicalVolumeAlreadyInLogicalGroupError(PartitionException): pass
class CannotDeleteLogicalVolumeFromLogicalGroupError(PartitionException): pass
class NotPhysicalVolumeError(PartitionException): pass
class InvalidVolumeGroupExtentSizeError(PartitionException): pass
class PhysicalVolumeStillInUseError(PartitionException): pass
class LogicalVolumeStillInUseError(PartitionException): pass
class LogicalVolumeGroupStillInUseError(PartitionException): pass
class MountFailedError(PartitionException): pass
class VolumeGroupHasBeenDeletedError(PartitionException): pass
class CannotDeleteVolumeGroupError(PartitionException): pass
class LVMInconsistencyError(PartitionException): pass
