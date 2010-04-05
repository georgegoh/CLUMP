#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: license_plugin.py 3557 2010-02-26 05:09:22Z qguan $
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

import re

from path import path

from primitive.support.util import runCommand
from kusu.license.license_manager import LIC_BUNDLE_PATH
import kusu.util.log as kusulog
logger = kusulog.getKusuLog('license.tool')


UNKNOWN_LICENSE = 0
DEMO_LICENSE = 1
SERVER_LICENSE = 2
NODELOCK_LICENSE = 3


class FlexlmProductLicense(object):
    """FLEXlm license data model class"""
    def __init__(self, product, features, installed, servers=None, daemon=None):
        self.product_name = product
        self.features = features
        self.servers = servers
        self.daemon = daemon

        self.license_type = UNKNOWN_LICENSE
        self.installed = installed

    def __str__(self):
        if not self.installed:
            return '%s (Product not installed)' % (self.product_name)
        return self.product_name

Restarted_lmgrd = False #to avoid restart lmgrd many times

class KusuLicensePluginBase(object):
    """kusu license tool plugin base class"""
    lmgrd_restarted = False

    def __init__(self, dbconn=None):
        self.dbconn = dbconn

        self.product_name = None
        self.product_desc = None
        self.product_ver = None

        self.feature_exact_rules = []
        self.feature_regex_rule = ''
        self.license_location = None
        self.daemon_path = None
        self.lmhostid_cmd = None
        self.services = []

        self.license = None

    def __str__(self):
        return self.product_desc or ''

    def isProductInstalled(self):
        """Get the product install status, plugin must override it"""
        raise NotImplementedError

    def checkLicenseDependency(self):
        """Check product license dependency, plugin can override it for special case"""
        return True

    def _loadExistingLicense(self):
        """Get the existing product license content from private location"""
        #TODO: Need implement it to compare the difference
        raise NotImplementedError

    def getLicenseType(self, license):
        """Get the license type from license content, plugin can override it for special case"""

        parts = license.features[0].split()[7:]
        if 'DEMO' in parts or 'HOSTID=DEMO' in parts:
            return DEMO_LICENSE

        if license.servers:
            return SERVER_LICENSE
        else:
            return NODELOCK_LICENSE

    def getLicenseWarning(self):
        """Get the product license prompt for firstboot script"""
        if self.license_location and not path(self.license_location).exists() and self.checkLicenseDependency():
            return "No license found for %s. Software license is required. Run kusu-license-tool to register.\n" % (self.product_desc)
        return ''

    def createProductLicense(self, server_list, daemon_list, feature_list):
        """Create a new product license object from the given feature list"""
        my_features = []
        for feature_line in feature_list:
            feature = feature_line.split()[1]
            if feature in self.feature_exact_rules:
                my_features.append(feature_line)
                continue

            if self.feature_regex_rule and re.match(self.feature_regex_rule, feature):
                my_features.append(feature_line)
                continue

        if my_features:
            lic = FlexlmProductLicense(self.product_name, my_features,
                                       self.isProductInstalled(), server_list, daemon_list)
            lic.license_type = self.getLicenseType(lic)
            return lic

    def applyLicense(self, product_license, unified=True, forced=False, product_license_path=None):
        """Apply the new product license object"""
        if not self.isProductInstalled():
            logger.warning('Product (%s) is not installed' % self.product_name)
            return
        logger.debug('Check license change for product (%s) when applying license, unified = %s' % (self.product_name, unified))

        self.license = product_license
        lic_link = path(self.license_location)
        if unified:
            if product_license:
                logger.info('Prepare new license file for product (%s)' % self.product_name)
                print 'Prepare new license file for product (%s).' % self.product_name
                if lic_link.exists():
                    lic_link.remove()
                if not lic_link.dirname().exists():
                    lic_link.dirname().makedirs()
                path(LIC_BUNDLE_PATH).symlink(self.license_location)
                return True

            elif lic_link.islink() and lic_link.realpath() == LIC_BUNDLE_PATH:
                #Not in the new unified license file, remove the existing link
                logger.info('Remove license file from product (%s)' % self.product_name)
                print 'Remove license file from product (%s).' % self.product_name
                lic_link.unlink()
                return True

            else:
                logger.debug('No license change needed for product (%s)' % self.product_name)

        elif product_license_path:
            print 'Prepare new license file for product (%s).' % self.product_name
            if not lic_link.dirname().exists():
                lic_link.dirname().makedirs()
            path(product_license_path).copy(self.license_location)
            return True

    def removeLicense(self):
        """Remove the existing product license"""
        if not self.isProductInstalled():
            logger.warning('Product (%s) is not installed' % self.product_name)
            return
        logger.debug('Check license change for product (%s) when removing license.' % self.product_name)

        lic_link = path(self.license_location)
        if lic_link.islink() and lic_link.realpath() == LIC_BUNDLE_PATH:
            logger.info('Remove license for product (%s)' % self.product_name)
            print 'Remove license for product (%s).' % self.product_name
            lic_link.unlink()
            return True

    def activateLicense(self):
        """Restart the service to enable/disable product license"""

        global Restarted_lmgrd
        remove_mode = not self.license
        restart_lmgrd = self.license and self.license.license_type == SERVER_LICENSE

        try:
            if (restart_lmgrd or remove_mode) and not Restarted_lmgrd:
                logger.info('Restart lmgrd service')
                print 'Restart lmgrd service'
                out, err = runCommand('/etc/init.d/lmgrd restart')
                if out:
                    logger.info(out)
                if err:
                    logger.error(err)
                runCommand('/sbin/pidof lmgrd')
                Restarted_lmgrd = True
        except:
            if not remove_mode:
                print 'Service (lmgrd) did not restart successfully. See lmgrd log for details.'
                return False

        try:
            print 'Restart services for product (%s)' % self.product_name
            return self.serviceAction()
        except Exception, e:
            if not remove_mode:
                print 'Product (%s) did not restart successfully. See product logs for details.' % self.product_name
                logger.error(e)
                return False
            return True

    def serviceAction(self):
        """Restart the service for product"""
        for service in self.services:
            logger.info('Restart %s service for product (%s)' % (service, self.product_name))
            out, err = runCommand('/etc/init.d/%s restart' % service)
            if out:
                logger.info(out)
            if err:
                logger.error(err)

        return True
