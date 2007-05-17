#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
import exceptions

class KusuError(exceptions.Exception): pass
class InvalidPath(KusuError): pass
class LoadDistroConfFailed(KusuError): pass
class HTTPError(Exception): pass
class FTPError(Exception): pass



