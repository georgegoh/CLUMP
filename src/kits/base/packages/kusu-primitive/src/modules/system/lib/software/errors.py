#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#

# General
class SystemException(Exception): pass
class ProbeException(SystemException): pass

# Probe Exception
class TimeZoneMissingException(ProbeException): pass
class KeyboardMissingException(ProbeException): pass
