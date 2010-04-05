#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: license_manager.py 3565 2010-03-01 03:30:16Z leiai $
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

import sys
from path import path

from primitive.support.util import runCommand

from kusu.util.errors import KusuError
import kusu.util.log as kusulog
logger = kusulog.getKusuLog('license.tool')

LIC_PLUGIN_DIR = '/opt/kusu/lib/plugins/licensetool'
LIC_BUNDLE_PATH = '/opt/kusu/license/bundle-license.dat'
LIC_BUNDLE_BAK_PATH = '/opt/kusu/license/bak'


class InvalidFlexlmFile(KusuError): pass
class InvalidFlexlmServer(InvalidFlexlmFile): pass
class InvalidFlexlmFeature(InvalidFlexlmFile): pass
class NoDefaultLicenseFile(KusuError): pass


class KusuLicenseSupportManager(object):
    """Kusu License support tool class"""

    def __init__(self):
        self.plugin_instances = {}

        self.force_mode = False
        self.specified_product = None
        self.license_location = None
        self.applied_licenses = {}

        self._loadPlugins()

    def _loadPlugins(self):
        """Loads all plugins for license tool."""

        plugin_dir = path(LIC_PLUGIN_DIR)
        if not plugin_dir.exists():
            return

        sys.path.append(LIC_PLUGIN_DIR)

        plugin_list = []
        for plugin in plugin_dir.glob('*.py'):
            module_name = plugin.splitext()[0].basename()
            plugin_list.append(module_name)
        # sort by plugin name: resolve sequence issue among these plugins.
        plugin_list.sort()
        
        # Create instances of each new plugin and store the instances.
        for plugin_name in plugin_list:
            try:
                module = __import__(plugin_name)
                plugin = module.KusuLicensePlugin()
                self.plugin_instances[plugin.product_name] = plugin
            except Exception, e:
                logger.debug(e)
                logger.warning("Invalid plugin '%s', this plugin will be IGNORED.\n" % module)

    def _handleLicenseLocation(self, default_location):
        """Check the license file location given by user""" 

        if self.license_location and path(self.license_location).realpath() == path(default_location).realpath():
            self.license_location = None

        if not self.license_location and not path(default_location).exists():
            raise NoDefaultLicenseFile, 'No default license file.'

        return self.license_location or default_location

    def parseLicense(self):
        """Read the content from license file and invoke plugins to parse the FLEXlm license object."""

        if not self.specified_product:
            #Not specified product name, in unified license mode
            license_location = self._handleLicenseLocation(path(LIC_BUNDLE_PATH))
            server_lines, daemon_lines, feature_lines = \
                               self._parseLicenseFile(license_location)

            for license in self._createLicenseForProducts(server_lines, daemon_lines, feature_lines):
                self.applied_licenses[license.product_name] = license
        else:
            #individual license mode
            plugin = self.plugin_instances[self.specified_product]

            license_location = self._handleLicenseLocation(plugin.license_location)
            server_lines, daemon_lines, feature_lines = \
                               self._parseLicenseFile(license_location)

            license = plugin.createProductLicense(server_lines, daemon_lines, feature_lines)
            if license:
                self.applied_licenses[license.product_name] = license

        if not self.applied_licenses:
            raise InvalidFlexlmFeature, 'No valid feature in license file.'

    def _parseLicenseFile(self, license_location):
        license_file = open(license_location)
        license_content = license_file.readlines()
        license_file.close()
        lmhostid = self._getLmhostid()
        out, err = runCommand('hostname')
        host_name = out.strip()

        server_lines = []
        daemon_lines = []
        feature_lines = []
        new_lines = []

        need_update = False
        found_hostid = False
        for line in license_content:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.startswith('SERVER'):
                if lmhostid and lmhostid in line:
                    found_hostid = True
                    license_host_name = line.split()[1]
                    need_update = license_host_name != host_name
                    if need_update:
                        line = line.replace(license_host_name, host_name)
                server_lines.append(line)

            elif line.startswith('DAEMON') or line.startswith('VENDOR'):
                daemon_lines.append(line)
            elif line.startswith('FEATURE') or line.startswith('INCREMENT'):
                feature_lines.append(line)
            else:
                logger.warning('Unknown line in %s: \n    %s' % (license_location, line))
            new_lines.append(line)

        if server_lines:
            if lmhostid and not found_hostid:
                raise InvalidFlexlmServer, 'The hostid in license file does not match.'
            if not daemon_lines:
                raise InvalidFlexlmFile, 'Invalid license file.'

            if need_update:
                path(license_location).write_lines(new_lines)
        elif daemon_lines:
            raise InvalidFlexlmFile, 'Invalid license file.'

        return server_lines, daemon_lines, feature_lines

    def _getLmhostid(self):

        try:
            for plugin in self.plugin_instances.values():
                if plugin.isProductInstalled() and plugin.lmhostid_cmd:
                    out, err = runCommand(plugin.lmhostid_cmd)
                    return out.strip()
        except:
            logger.error('Could not get the lmhostid.')

    def _createLicenseForProducts(self, server_list, daemon_list, feature_list):
        products = []
        for plugin in self.plugin_instances.values():
            product = plugin.createProductLicense(server_list, daemon_list, feature_list)
            if product:
                products.append(product)
        return products

    def register(self):
        """The license registration action."""
        unified_flag = not self.specified_product
        if not unified_flag:
            plugin = self.plugin_instances[self.specified_product]
            if plugin.applyLicense(self.applied_licenses.get(self.specified_product),
                                   unified_flag, self.force_mode, self.license_location):
                plugin.activateLicense()
        else:
            #now begin to apply license for unified license file
            self._preApplyingUnifiedLicense()

            activated_plugins = []
            for product, plugin in self.plugin_instances.items():
                license = self.applied_licenses.get(product)
                if plugin.applyLicense(license, unified_flag, self.force_mode, self.license_location):
                    if not plugin.activateLicense() and not self.force_mode:
                        break

    def remove(self):
        """The license remove action."""
        activated_plugins = []
        for product, plugin in self.plugin_instances.items():
            if plugin.removeLicense():
                activated_plugins.append(plugin)

        license_file = path(LIC_BUNDLE_PATH)
        if license_file.exists():
            license_file.remove()

        for plugin in activated_plugins:
            plugin.activateLicense()

    def _preApplyingUnifiedLicense(self):
        """The preparation steps before applying a unified license."""
        backup_dir = path(LIC_BUNDLE_BAK_PATH)
        if not backup_dir.exists():
            backup_dir.makedirs()

        old_license_file = path(LIC_BUNDLE_PATH)
        if self.license_location:
            if old_license_file.exists():
                old_license_file.copy(backup_dir)
            path(self.license_location).copy(old_license_file)

