import os
import snack
from kusu.ngedit.ngedit import NGEPluginBase

class NGPlugin(NGEPluginBase):
    name= 'Base Installer plugin screen #2'
    msg = 'This is a non-interactive component plugin'

    def __init__(self, database, kusuApp=None, gridWidth=45):
        NGEPluginBase.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.setHelpLine("Help Line for base-installer component's plugin screen")

    def add(self):
        assert(self.ngid)
        os.system("touch /tmp/KuSu_%s_add" %self.ngid)

    def remove(self):
        assert(self.ngid)
        if os.path.exists("/tmp/KuSu_%s_add" %self.ngid):
            os.remove("/tmp/KuSu_%s_add" %self.ngid)
            #os.system("rm /tmp/KuSu_%s_add" %self.ngid)
