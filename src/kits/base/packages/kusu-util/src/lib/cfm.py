#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
import path
import sys
try:
    import subprocess
except:
    from popen5 import subprocess

from kusu.core import database as db
from kusu.core import app
from kusu.cfms import PackBuilder

def get_readonly_dbs():
    DB_NAME = 'kusudb'
    DB_USER = 'nobody'
    DB_PASSWORD = None

    dbdriver = os.getenv('KUSU_DB_ENGINE', 'postgres')
    return db.DB(dbdriver, DB_NAME, DB_USER, DB_PASSWORD)

def updateCfmfiles():
    """Update cfmfiles.lst"""
    kApp = app.KusuApp(dummy_app=True)
    _ = kApp.langinit()
    pb = PackBuilder(kApp.errorMessage, kApp.stdoutMessage)
    pb.genMergeFiles()
    pb.updateCFMdir()
    pb.removeOldFiles()
    pb.genFileList()

def updateCfmPackages(ngname=''):
    """Update /opt/kusu/cfm/<ngid>.package.lst"""
    def foo(*args): pass
    pb = PackBuilder(foo, foo)
    pb.getPackageList(ngname)

def runCfmMaintainerScripts():
    """
    Runs all CFM maintainer scripts found in
    {DEPOT_KITS_ROOT}/<kid>/cfm/*.rc.py
    """
    try:
        dbs = get_readonly_dbs()
        kits_root = dbs.AppGlobals.selectfirst_by(kname='DEPOT_KITS_ROOT').kvalue
    except:
        kits_root = '/depot/kits'

    scripts = path.path(kits_root).glob('*/cfm/*.rc.py')
    scripts_run = []
    for script in scripts:
        # Skip duplicate scripts
        if script.basename() in scripts_run:
            continue
        cmd = '/opt/kusu/bin/kusurc %s' % script
        p = subprocess.Popen(cmd,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        scripts_run.append(script.basename())

    # Redirect all stdout, stderr
    oldOut = sys.stdout
    oldErr = sys.stderr
    f = open('/dev/null', 'w')
    sys.stdout = f
    sys.stderr = f

    # Update cfmfiles.lst
    updateCfmfiles()

    # Restore stdout and stderr
    sys.stdout = oldOut
    sys.stderr = oldErr
    f.close()
