#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import rcplugin 

class KusuRC(rcplugin.Plugin):

    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'Migrate AppGlobals'
        self.desc = 'Setting appglobals variables'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        new_values = { 'DEPOT_KITS_ROOT': '/depot/kits',
                       'DEPOT_DOCS_ROOT': '/depot/www/kits',
                       'DEPOT_IMAGES_ROOT': '/depot/images',
                       'DEPOT_REPOS_ROOT': '/depot/repos',
                       'DEPOT_REPOS_SCRIPTS': '/depot/repos/custom_scripts',
                       'DEPOT_REPOS_POST': '/depot/repos/post_scripts',
                       'DEPOT_CONTRIB_ROOT': '/depot/contrib',
                       'DEPOT_UPDATES_ROOT': '/depot/updates',
                       'DEPOT_AUTOINST_ROOT': '/depot/repos/instconf',
                       'PIXIE_ROOT': '/tftpboot/kusu',
                       'PROVISION': 'KUSU' }

        for k,v in new_values.iteritems():
            r = self.dbs.AppGlobals.selectfirst_by(kname=k)
            if r:
                r.kvalue = v
            else:
                r = self.dbs.AppGlobals(kname=k, kvalue=v)
            r.flush()
        return True
