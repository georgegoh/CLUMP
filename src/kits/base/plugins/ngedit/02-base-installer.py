import snack
from kusu.ui.text.USXscreenfactory import USXBaseScreen,ScreenFactory
from kusu.ui.text.USXnavigator import *
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB

class NGPlugin(USXBaseScreen):
    name= 'Base Installer plugin screen #2'
    msg = 'This is a non-interactive component plugin'
    buttons = ['next_button', 'prev_button']
    hotkeysDict = {}

    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.setHelpLine("Help Line for base-installer component's plugin screen")
        self.ngid = None
        self.interactive = False

    def add(self):
        assert(self.ngid)

    def remove(self):
        assert(self.ngid)

    def isInteractive(self):
        return self.interactive
