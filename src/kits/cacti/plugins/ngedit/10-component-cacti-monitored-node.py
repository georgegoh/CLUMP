import os
import snack
from kusu.ngedit.ngedit import NGEPluginBase

class NGPlugin(NGEPluginBase):
    #name= 'Base Installer plugin screen #2'
    #msg = 'This is a non-interactive component plugin'

    def __init__(self, database, kusuApp=None, gridWidth=45):
        NGEPluginBase.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        #self.setHelpLine("Help Line for base-installer component's plugin screen")

    def common(self):
        os.system('/opt/cacti/bin/cacti.py | mysql -u root cacti')

    def add(self):
        self.common()

    def remove(self):
        self.common()

