#!/usr/bin/env python

import subprocess
import ycp
networkCards = ycp.SCR.Read(ycp.Path('.probe.netcard'))

for card in networkCards:
    module = card['drivers'][0]['modules'][0][0]
    cmd = 'modprobe %s' % module
    print cmd
    subprocess.call(cmd, shell=True)
