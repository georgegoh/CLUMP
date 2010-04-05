#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA


import os
import sys
from path import path
from kusu.core import database as db
from kusu.core.app import KusuApp
import kusu.util.log as kusulog
from optparse import OptionParser

db_driver = os.getenv('KUSU_DB_ENGINE', 'postgres')
db_name = 'kusudb'
db_user = 'apache'
dbs = db.DB(db_driver, db_name, db_user)


CMD_POSSIBLE_ACTIONS = ['add', 'remove']
CMD_POSSIBLE_KEYS = ['LMGRD_PATH', 'LM_LICENSE_FILE']

class LicenseSupportApp(KusuApp):

    def __init__(self):

        KusuApp.__init__(self)
        usage = """kusu-lmgrd-support [-h | --help]
                          [-v | --version]
                          action key path

    Possible action:
        add
        remove

    Possible key:
        LMGRD_PATH
        LM_LICENSE_FILE

    For example:
        kusu-lmgrd-support add LMGRD_PATH /path/to/lmgrd
        kusu-lmgrd-support remove LMGRD_PATH /path/to/lmgrd
        
        kusu-lmgrd-support add LM_LICENSE_FILE /path/to/license.dat
        kusu-lmgrd-support remove LM_LICENSE_FILE /path/to/license.dat
    """
        usage = self._(usage)
        self.parser = OptionParser(usage)
        self.parser.add_option('-v', '--version', dest='version', action="store_true", help=self._('Display version of tool'))

    
    def getVersion(self):
        self.stdoutMessage('kusu-lmgrd-support version %s\n', self.version)
        sys.exit(0)

    def checkArgs(self, args):
       
        if not args or len(args) < 3:
            self.parser.print_help()
            sys.stderr.write('Invalid arguments provided.\n')
            sys.exit(1)

        action = args[0]

        if action not in CMD_POSSIBLE_ACTIONS:
            self.parser.print_help()
            sys.stderr.write('Invalid action. Possible action is: %s.\n' % '|'.join(CMD_POSSIBLE_ACTIONS))
            sys.exit(1)

        key = args[1]

        if key not in CMD_POSSIBLE_KEYS:
            self.parser.print_help()
            sys.stderr.write('Invalid key. Possible key is: %s.\n' % '|'.join(CMD_POSSIBLE_KEYS))
            sys.exit(1)

        value = args[2]

        return (action, key, value)

 
    def appglobals_append_value_to_key(self, new_value, kname, separator=':'):
        """ Append a new_value to the end of the kvalue
            represented by the given kname in AppGlobals table.
        """
        # each record in AppGlobals table is a (kname,kvalue) pair.
        kv_pair = dbs.AppGlobals.selectfirst_by(kname=kname)

        # no value exists, so just create the new element.
        if not kv_pair:
            dbs.AppGlobals(kname=kname, kvalue=new_value).flush()
            return
        
        # append new value to the existing list if it is
        # not already in the list.
        current_values = []
        if kv_pair.kvalue: current_values = kv_pair.kvalue.split(separator)

        if new_value not in current_values:
            kv_pair.kvalue = separator.join(current_values + [new_value.strip()])
            kv_pair.flush()

        return


    def appglobals_remove_value_from_key(self, value, kname, separator=':'):
        """ Remove value from the kvalue represented 
            by the given kname in AppGlobals table.
        """
        # each record in AppGlobals table is a (kname,kvalue) pair.
        kv_pair = dbs.AppGlobals.selectfirst_by(kname=kname)

        # no value exists, nothing to do.
        if not kv_pair or not kv_pair.kvalue:
            return

        # remove value from the existing list if it exists.
        values = kv_pair.kvalue.split(separator)
        if value in values:
            values.remove(value)

            # join all elements again and commit.
            kv_pair.kvalue = separator.join(values)
            kv_pair.flush()
            
        return

      
    def run(self):
        (options, args) = self.parser.parse_args()

        if options.version: 
            self.getVersion()
        
        action, key, value = self.checkArgs(args)

        if action == 'add':
            self.appglobals_append_value_to_key(value, key)

        elif action == 'remove':
            self.appglobals_remove_value_from_key(value, key)

if __name__ == '__main__':

    if os.getuid() != 0:
        print 'You must be root to run this tool'
        sys.exit(1)

    kl = kusulog.getKusuLog()
    kl.addFileHandler(os.environ['KUSU_LOGFILE'])

    LicenseSupportApp().run()

