#!/usr/bin/env python
# $Id$
#
# Kusu Exceptions.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

# General
class KusuError(Exception): pass
class InvalidPathError(KusuError): pass
class UnknownTypeError(KusuError): pass
class UnknownFileTypeError(KusuError): pass
class FileDoesNotExistError(KusuError): pass
class FileAlreadyExistError(KusuError): pass
class FileReadPermissionError(KusuError): pass
class DirDoesNotExistError(KusuError): pass
class DirAlreadyExistError(KusuError): pass
class CommandFailedToRunError(KusuError): pass
class UserExitError(KusuError): pass
class UnknownDeviceError(KusuError): pass
class NotImplementedError(KusuError): pass
class UnsupportedURIError(KusuError): pass
class UnsupportedOS(KusuError): pass
class InvalidArguments(KusuError): pass

# partitiontool
class PartitionSchemaError(KusuError): pass
class DiskProfileNotEmptyError(KusuError): pass
class NoDisksFoundError(KusuError) : pass
class OutOfSpaceError(KusuError): pass
class DuplicateNameError(KusuError): pass
class DuplicateMountpointError(KusuError): pass
class NameNotFoundError(KusuError): pass
class UnknownPartitionTypeError(KusuError): pass
class PartitionSizeTooLargeError(KusuError): pass
class CannotDeleteExtendedPartitionError(KusuError): pass
class MountpointAlreadyUsedError(KusuError): pass
class CannotLabelPartitionError(KusuError): pass

# partitiontool - LVM errors
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
class LogicalVolumeGroupStillInUseError(KusuError): pass
class MountFailedError(KusuError): pass
class VolumeGroupHasBeenDeletedError(KusuError): pass
class CannotDeleteVolumeGroupError(KusuError): pass
class LVMInconsistencyError(KusuError): pass

# util.tools
class CopyFailedError(KusuError): pass
class NotSupportedURIError(KusuError): pass

# util.distro
class LoadDistroConfFailedError(KusuError): pass
class HTTPError(KusuError): pass
class FTPError(KusuError): pass

# util.net
class StartIPNotInNetError(KusuError): pass
class NoFreeIPError(KusuError): pass

# networktool
class InterfaceNotBroughtUpError(KusuError): pass
class InterfaceNotBroughtDownError(KusuError): pass
class FailedDHCPRequestError(KusuError): pass
class FailedSetStaticIPError(KusuError): pass
class NotSupportedOperatingSystem(KusuError): pass
class InterfaceNotFound(KusuError): pass

# autoinstall
class ProfileNotCompleteError(KusuError): pass
class TemplateNotFoundError(KusuError): pass
class UnableToGenerateFileFromTemplateError(KusuError): pass

# kitops
class KitopsError(KusuError): pass
class CannotMountKitMediaError(KitopsError): pass
class UnrecognizedKitMediaError(KitopsError): pass
class KitAlreadyInstalledError(KitopsError): pass
class InvalidKitInfoError(KitopsError): pass
class ComponentAlreadyInstalledError(KitopsError): pass
class KitNotInstalledError(KitopsError): pass
class InstallKitRPMError(KitopsError): pass
class CopyOSMediaError(KitopsError): pass
class DeleteKitsError(KitopsError): pass
class UpdateKitError(KitopsError): pass

# kits
class CannotAddKitError(KusuError): pass

# core.database
class NoSuchDBError(KusuError): pass
class UnsupportedDriverError(KusuError): pass
class UsernameNotSpecifiedError(KusuError): pass
class NoSuchColumnError(KusuError): pass
class NotSupportedDatabaseCreationError(KusuError): pass
class FailedToCreateDatabase(KusuError): pass
class FailedToDropDatabase(KusuError): pass
class UnableToCommitDataError(KusuError): pass
class UnableToSaveDataError(KusuError): pass

# repoman
class RepoNotCreatedError(KusuError): pass
class RepoOSKitError(KusuError): pass
class CannotCreateRepoError(KusuError): pass
class YumRepoNotCreatedError(KusuError): pass
class NodeGroupNotFoundError(KusuError): pass
class RepoNotFoundError(KusuError): pass
class ReposIntegrityError(KusuError): pass
class RepoCannotDeleteError(KusuError): pass
class NodeGroupHasRepoAlreadyError(KusuError): pass
class UpdatesImgNotCreatedError(KusuError): pass

# repoman.rhn
class rhnError(KusuError): pass
class rhnInvalidLoginError(KusuError): pass
class rhnInvalidSystemError(KusuError): pass
class rhnURLNotFound(KusuError): pass
class rhnUnknownError(KusuError): pass
class rhnServerError(KusuError): pass
class rhnUnknownMethodError(KusuError): pass
class rhnNoBaseChannelError(KusuError): pass
class rhnFailedDownloadRPM(KusuError): pass
class rhnInvalidServerID(KusuError): pass
class rhnNoAccountInformationProvidedError(KusuError): pass
class rhnSystemNotRegisterd(KusuError): pass

# repoman.you
class youNoAccountInformationProvidedError(KusuError): pass

# repoman.yum
class repodataChecksumError(KusuError): pass

# repoman.updates
class UnableToPrepUpdateKit(KusuError): pass
class UnableToMakeUpdateKit(KusuError): pass
class UnableToExtractKernel(KusuError): pass
class UnableToUpdateInitrdKernel(KusuError): pass
class InvalidInitrd(KusuError): pass

# b-m-t
class FilePathError(KusuError): pass
class NotPriviledgedUser(KusuError): pass
class UnsupportedPackingType(KusuError): pass
class ToolNotFound(KusuError): pass
class CopyError(KusuError): pass
class FileAlreadyExists(KusuError): pass
class InvalidInstallSource(KusuError): pass
class UnsupportedDistro(KusuError): pass
class InvalidKusuSource(KusuError): pass
class FailedBuildCMake(KusuError): pass
class FailedBuildMake(KusuError): pass
class KitCopyError(KusuError): pass

# nodeinstaller
class NIISourceUnavailableError(KusuError): pass
class EmptyNIISource(KusuError): pass
class ParseNIISourceError(KusuError): pass
class InvalidPartitionSchema(KusuError): pass
class LVMPreservationError(KusuError): pass

# buildkit
class KitSrcAlreadyExists(KusuError): pass
class PackageBuildError(KusuError): pass
class KitBuildError(KusuError): pass
class KitscriptValidateError(KusuError): pass
class UnknownPackageType(KusuError): pass
class UndefinedOSType(KusuError): pass
class UnsupportedNGType(KusuError): pass
class UndefinedComponentInfo(KusuError): pass
class UndefinedKitInfo(KusuError): pass
class InvalidBuildProfile(KusuError): pass
class PackageAttributeNotDefined(KusuError): pass
class KitDefinitionEmpty(KusuError): pass
class UnsupportedScriptMode(KusuError):pass
class KitinfoSyntaxError(KusuError): pass
class BuildkitArchError(KusuError): pass

# util.rpmtool
class InvalidRPMHeader(KusuError): pass
class RPMComparisonError(KusuError): pass

# driverpatch
class UnknownKernelModuleAsset(KusuError): pass


