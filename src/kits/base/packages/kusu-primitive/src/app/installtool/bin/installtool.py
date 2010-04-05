#!/usr/bin/env python
# $Id: installtool.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
''' InstallTool is used to generate output based on SLES autoinst.xml or 
    RHEL kickstart-ks.cfg formats based on inputs as specified in UBI-7.
'''
DEBUG=False
import sys
from path import path
from primitive.installtool.commands import GenerateAutoInstallScriptCommand

if len(sys.argv) <= 1:
    sys.exit('Config file not provided.')

p = path(sys.argv[1])
if not p.exists():
    sys.exit('%s does not exist' % p)

config_path = p.realpath()[0:p.rfind(p.name)]
sys.path.append(config_path)
config = __import__(p.namebase)

if DEBUG:
    print config.template_uri
    print config.output
    print config.os
    print config.installsrc
    print config.rootpw
    print config.tz
    print config.lang
    print config.keyboard
    print config.networkprofile
    print config.packages

instnum = ''
if hasattr('config', 'instnum'):
    instnum = config.instnum

ic = GenerateAutoInstallScriptCommand(os=config.os,
                                      diskprofile=None,
                                      networkprofile=config.networkprofile,
                                      installsrc=config.installsrc,
                                      rootpw=config.rootpw,
                                      tz=config.tz,
                                      lang=config.lang,
                                      keyboard=config.keyboard,
                                      packageprofile=config.packages,
                                      diskorder=[],
                                      instnum=instnum,
                                      template_uri=config.template_uri,
                                      outfile=config.output)

ic.execute()
