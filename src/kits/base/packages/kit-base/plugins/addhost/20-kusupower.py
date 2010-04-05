# Copyright (C) 2010 Platform Computing Inc.

KUSUPWR_CONF='/opt/kusu/etc/kusu-power.conf'

import os
from kusu.addhost import *


class AddHostPlugin(AddHostPluginBase):
    def updated(self):
        os.system("/opt/kusu/bin/kusu-genconfig kusupower_conf %s > %s.new" % (KUSUPWR_CONF, KUSUPWR_CONF))
        os.chmod("%s.new" % KUSUPWR_CONF, 0400)
        os.system("mv %s.new %s" % (KUSUPWR_CONF, KUSUPWR_CONF))

    def finished(self, nodelist, prePopulateMode):
        os.system("/opt/kusu/bin/kusu-genconfig kusupower_conf %s > %s.new" % (KUSUPWR_CONF, KUSUPWR_CONF))
        os.chmod("%s.new" % KUSUPWR_CONF, 0400)
        os.system("mv %s.new %s" % (KUSUPWR_CONF, KUSUPWR_CONF))
