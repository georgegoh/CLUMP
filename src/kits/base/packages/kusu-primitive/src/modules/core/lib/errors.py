#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# 
# $Id: errors.py 3201 2009-11-12 10:18:36Z binxu $ 
# 
# Copyright (C) 2010 Platform Computing Inc. 
# 

"""Exception handling follows the SOA model where logical functionality is
grouped together and packaged as cooperating services. With these logical
separations, robust error handling can be introduced by structuring the
exception hierarchy such that each layer(application, command, module)
can inherit from their respective exception superclasses.

By catching the Application, Command, or Module exceptions related to
the code called, the caller can be certain that exceptions raised there
will be caught."""

class PrimitiveException(Exception): pass

class ApplicationException(PrimitiveException): pass
class CommandException(PrimitiveException): pass
class ModuleException(PrimitiveException): pass


# General - legacy stuff kept so as not to break anything
class PrimitiveError(Exception): pass

class InvalidPathError(PrimitiveError): pass
class UnknownTypeError(PrimitiveError): pass
class UnknownFileTypeError(PrimitiveError): pass
class FileDoesNotExistError(PrimitiveError): pass
class FileAlreadyExistError(PrimitiveError): pass
class FileReadPermissionError(PrimitiveError): pass
class DirDoesNotExistError(PrimitiveError): pass
class DirAlreadyExistError(PrimitiveError): pass
class CommandFailedToRunError(PrimitiveError): pass
class UserExitError(PrimitiveError): pass
class UnknownDeviceError(PrimitiveError): pass
class NotImplementedError(PrimitiveError): pass
class UnsupportedURIError(PrimitiveError): pass
class UnsupportedOS(PrimitiveError): pass
class CommandMissingArgsError(PrimitiveError): pass

# Autoinstall exceptions
class TemplateNotFoundException(PrimitiveError): pass
class AutoInstallConfigNotCompleteException(PrimitiveError): pass

# Fetchtool exceptions
class FetchException(PrimitiveError): pass
class HTTPAuthException(PrimitiveError): pass
class UnknownHostException(PrimitiveError): pass
class CommandMissingArgsException(PrimitiveError): pass
class InvalidUserPassPairException(PrimitiveError): pass
class ExistingDestCannotBeOverwrittenException(PrimitiveError): pass

#Proxy exceptions
class ProxyException(PrimitiveError): pass
class ProxyAuthException(ProxyException): pass
class UnknownProxyHostException(ProxyException): pass
class UnsupportedProxyProtocolException(ProxyException): pass
class BadProxyURIFormatException(ProxyException): pass

# RHN exceptions
class RHNException(PrimitiveError): pass
class RHNServerException(RHNException): pass
class RHNUnknownMethodException(RHNException): pass
class RHNInvalidLoginException(RHNException): pass
class RHNInvalidSystemException(RHNException): pass
class RHNNoBaseChannelException(RHNException): pass
class RHNURLNotFoundException(RHNException): pass

