#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: kusu-license-tool.py 3510 2010-02-12 06:27:11Z binxu $
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

import os
import sys
from optparse import OptionParser
import tempfile
import atexit
from path import path

from kusu.core.app import KusuApp
from kusu.license.license_manager import KusuLicenseSupportManager, LIC_BUNDLE_BAK_PATH, LIC_BUNDLE_PATH
from kusu.license.license_manager import InvalidFlexlmFile, NoDefaultLicenseFile
import kusu.util.log as kusulog


class LicenseOptionParser(OptionParser):

    plugin_instances = None

    def print_help(self):
        OptionParser.print_help(self)

        print """
actions:

  register    Apply new license to products
  recover     Recover the backup license
"""

        self._print_support_option()

    def _print_support_option(self):
        print 'supported products:\n'
        for product, plugin in self.plugin_instances.items():
            product_desc = str(plugin)
            if not plugin.isProductInstalled():
                product_desc += ' (Not installed)'
            elif plugin.license_location:
                product_desc += ' (default license in ' + plugin.license_location + ')'
            print '  %-12s%s' % (product, product_desc)

    def _add_version_option(self):
        self.add_option("-v", "--version",
                        action="version",
                        help="show program's version number and exit")


class KusuLicenseToolApp(KusuApp):
    """Kusu License Tool Main application class"""

    def __init__(self):
        KusuApp.__init__(self)

        self.action_handlers = {
            'register': self.register_handler,
            'recover': self.recover_handler,
        }

    def register_handler(self):
        #Handler for 'register' action
        parser = OptionParser(usage='%prog register [options]')
        parser.add_option("-f", "--file",
                          action="store", type="string", dest="license",
                          help=self._("License file to be applied"))
        parser.add_option("-p", "--product",
                          action="store", type="string", dest="product",
                          help=self._("Product to apply the license for"))
        parser.add_option("", "--force",
                          action="store_true", dest="force",
                          help=self._("Forced registration mode"))
        (options, args) = parser.parse_args(args=sys.argv[2:])
        if args:
            parser.print_help()
            sys.exit(1)

        if options.license and not path(options.license).exists():
            sys.stderr.write('The specified license file does not exist.\n')
            sys.exit(1)

        if options.license and path(options.license).isdir():
            sys.stderr.write('License file cannot be a directory. Specify a valid license file.\n')
            sys.exit(1)

        if options.product and options.product not in self.lic_mgr.plugin_instances:
            sys.stderr.write('The specified product is not supported.\n')
            sys.exit(1)

        self.lic_mgr.license_location = options.license
        self.lic_mgr.specified_product = options.product
        self.lic_mgr.force_mode = options.force

        if options.product:
            self._registerIndividualLicense()
        else:
            self._registerUnifiedLicense()

    def _registerIndividualLicense(self):
        try:
            self.lic_mgr.parseLicense()
            if not self.confirm("Do you wish to continue?", "yes/NO", "no"):
                sys.exit(0)

            self.lic_mgr.register()
        except InvalidFlexlmFile, e:
            sys.stderr.write('%s\n' % e)
            sys.exit(1)
        except NoDefaultLicenseFile:
            sys.stderr.write('Invalid license file.\n')
            sys.exit(1)

    def _registerUnifiedLicense(self):
        try:
            self.lic_mgr.parseLicense()
            print 'The provided license file contains:'
            for proc_lic in self.lic_mgr.applied_licenses.values():
                print '  %s' % proc_lic,
            print

            if not self.confirm("Do you wish to continue?", "yes/NO", "no"):
                sys.exit(0)

            self.lic_mgr.register()
        except InvalidFlexlmFile, e:
            sys.stderr.write('%s\n' % e)
            sys.exit(1)
        except NoDefaultLicenseFile:
            if self.confirm("%s does not exist. Do you mean to remove the license?" % LIC_BUNDLE_PATH, "yes/NO", "no"):
                self.lic_mgr.remove()


    def remove_handler(self):
        #Handler for 'remove' action
        parser = OptionParser(usage='%prog remove')
        (options, args) = parser.parse_args(args=sys.argv[2:])
        if args:
            parser.print_help()
            sys.exit(1)
        if not self.confirm("This will remove all license. Do you wish to continue?", "yes/NO", "no"):
            sys.exit(0)

        self.lic_mgr.remove()

    def recover_handler(self):
        #Handler for 'recover' action
        parser = OptionParser(usage='%prog recover')
        (options, args) = parser.parse_args(args=sys.argv[2:])
        if args:
            parser.print_help()
            sys.exit(1)

        backup_lic = path(LIC_BUNDLE_BAK_PATH) / path(LIC_BUNDLE_PATH).basename()
        if not backup_lic.exists():
            sys.stderr.write('The backup license file does not exist.\n')
            sys.exit(1)

        tmp_license = path(tempfile.mktemp(prefix='kusu-license-tool'))
        atexit.register(self.cleanup, tmp_license)

        backup_lic.copy(tmp_license)
        self.lic_mgr.license_location = str(tmp_license)

        try:
            self.lic_mgr.parseLicense()
            print 'The license to be recovered contains:'
            for proc_lic in self.lic_mgr.applied_licenses.values():
                print '  %s' % proc_lic

            if not self.confirm("Do you wish to continue?", "yes/NO", "no"):
                sys.exit(0)

            self.lic_mgr.register()
        except InvalidFlexlmServer:
            sys.stderr.write('The hostid in license file does not match.\n')
            sys.exit(1)
        except InvalidFlexlmFeature:
            sys.stderr.write('Invalid license file.\n')
            sys.exit(1)

    def run(self):
        parser = LicenseOptionParser(usage="%prog <action> [options]",
                                     version='%prog version ' + self.version)
        self.lic_mgr = KusuLicenseSupportManager()
        parser.plugin_instances = self.lic_mgr.plugin_instances
        parser.disable_interspersed_args()
        (options, args) = parser.parse_args()

        if not args:
            parser.print_help()
            sys.exit(1)

        action = args[0]
        if not action in self.action_handlers:
            sys.stderr.write('Error: unrecognized action \"%s\"\n' % (action))
            sys.exit(1)

        if not [x for x in self.lic_mgr.plugin_instances.values() if x.isProductInstalled()]:
            sys.stderr.write('Error: No supported product installed.\n')
            sys.exit(1)

        self.action_handlers[action]()

    def confirm(self, question, alternatives, defaultvalue):

        try:
            response = raw_input("Q: %s [%s]: " % (question, alternatives))
        except KeyboardInterrupt:
            sys.stderr.write("\n\nTerminating kusu-license-tool due to user pressing <ctrl>-c\n")
            sys.exit(1)

        if not response:
            response = defaultvalue
        result = response.strip().lower() in ['yes', 'y']
        if not result:
            print 'You have cancelled the operation.\n'

        return result

    def cleanup(self, tmpfile):
        if tmpfile.exists():
            tmpfile.remove()


if __name__ == "__main__":
    logger = kusulog.getKusuLog()
    logger.addFileHandler('/var/log/kusu/kusu-license-tool.log')

    if os.getuid() != 0:
        sys.stderr.write('Only root user can run kusu-license-tool.\n')
        sys.exit(1)

    app = KusuLicenseToolApp()
    app.run()
