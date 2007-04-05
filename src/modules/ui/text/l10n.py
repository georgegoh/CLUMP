#!/usr/bin/env python
# $Id$
#
# Common localization routine for Kusu.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
"""This module shows a simplified example of using the ScreenFactory classes."""
__version__ = "$Revision$"
import gettext

try:
    t = gettext.translation('kusu', 'locale')
except IOError:
    t = gettext.translation('kusu', '/usr/share/locale')
t.install()
