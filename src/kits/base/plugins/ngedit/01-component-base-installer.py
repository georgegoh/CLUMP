import os
import glob
import snack
from kusu.ngedit.ngedit import NGEPluginBase

class NGPlugin(NGEPluginBase):
    name= 'Base Installer Plugin Screen'
    msg = 'This component plugin screen is interactive'

    def __init__(self, database, kusuApp=None, gridWidth=45):
        NGEPluginBase.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.setHelpLine("Help for base-installer component's plugin screen")
        self.interactive = True

    def drawImpl(self):
        """
        All screen drawing code goes here. Don't draw the buttons as well, this
        is already done for you.
        """
        self.screenGrid = snack.Grid(1, 1)
        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                 width=self.gridWidth),
                                 col=0, row=0)

    def add(self):
        assert(self.ngid)
        query = "select kvalue from appglobals where kname = 'CFMBaseDir'"
        self.database.execute(query)
        rv = self.database.fetchone()
        
        fname = os.tempnam('/tmp','bAsE-')
        fp = file(fname,'w')
        fp.write('this is a config file\nngid=%s\n' %self.ngid)
        fp.write('CFM Base Dir = %s\n' %rv[0])
        fp.close()

    def remove(self):
        assert(self.ngid)
        # remove configuration files
        flist = glob.glob('/tmp/bAsE-*')
        for f in flist:
            os.remove(f)
