#!/usr/bin/env python
# $Id$
import os

try:
    os.remove('MANIFEST')               # to avoid those bloody out-of-date manifests!!
except:
    pass
    
import SetupTools
import SetupConfig
configurations = (SetupConfig,)
SetupTools.run_setup( configurations )




