#!/usr/bin/env python

from kusu.core import rcplugin

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'initrd-templates'
        self.desc = 'Initializing initrd-templates'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        self.runCommand('/opt/kusu/sbin/mkinitrd-templates')
        return True

if __name__ == "__main__":
    krc = KusuRC()
    krc.run()