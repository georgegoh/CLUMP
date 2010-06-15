#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
from path import path
from kusu.license.license_manager import KusuLicenseSupportManager
import kusu.util.log as kusulog

SET_MOTD=False

def displayLicensing():
    registration_message = ''
    lic_mgr = KusuLicenseSupportManager()
    for product, plugin in lic_mgr.plugin_instances.items():
        if plugin.isProductInstalled():
            registration_message += plugin.getLicenseWarning()

    if registration_message:
        print '\n' + registration_message

    return registration_message

def run():

    message = displayLicensing()

    return True


if __name__ == "__main__":
    logger = kusulog.getKusuLog()
    logger.addFileHandler('/var/log/kusu/kusu-license-tool.log')

    run()
