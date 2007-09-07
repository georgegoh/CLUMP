import os
import snack
from kusu.ngedit import NGEPluginBase

class NGPlugin(NGEPluginBase):
    name= 'Lava NGEdit Plugin'
    msg = 'This is a non-interactive component plugin'

    def __init__(self, database, kusuApp=None, gridWidth=45):
        NGEPluginBase.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.setHelpLine("Lava Kit")

    def add(self):
        assert(self.ngid)
	query = ('select ngname from nodegroups where ngid = %s' % self.ngid)
	try:
	    database.execute(query)
	    ngname = database.fetchone()
	except:
            return
   
	os.system('mkdir -p \"/etc/cfm/%s/opt/lava/conf\"' % ngname)

    def remove(self):
        assert(self.ngid)
        query = ('select ngname from nodegroups where ngid = %s' % self.ngid)
        try:
            database.execute(query)
            ngname = database.fetchone()
        except:
            return

        os.system('rm -rf \"/etc/cfm/%s/opt/lava/conf\"' % ngname)
