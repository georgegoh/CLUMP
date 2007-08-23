import os
import glob
import snack
from kusu.ngedit import NGEPluginBase

class NGPlugin(NGEPluginBase):
    name= 'Base Node Plugin Screen'
    msg = 'Interactive component plugin screen for base-node'

    def __init__(self, database, kusuApp=None, gridWidth=45):
        NGEPluginBase.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.setHelpLine("Help for base-node component's plugin screen")
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

    def remove(self):
        assert(self.ngid)
