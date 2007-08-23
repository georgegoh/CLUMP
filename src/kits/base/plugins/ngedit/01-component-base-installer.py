import snack
from kusu.ui.text.USXscreenfactory import USXBaseScreen,ScreenFactory
from kusu.ui.text.USXnavigator import *
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB
import glob
import os

class NGPlugin(USXBaseScreen):
    name= 'Base Installer Plugin Screen'
    msg = 'This component plugin screen is interactive'
    buttons = ['next_button', 'prev_button']
    hotkeysDict = {}

    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.setHelpLine("Help for base-installer component's plugin screen")
        self.ngid = None
        self.interactive = True

    def isInteractive(self):
        return self.interactive

    def setCallbacks(self):

        #for the buttons
        self.buttonsDict['next_button'].setCallback_(self.myNextAction)
        self.buttonsDict['prev_button'].setCallback_(self.myPrevAction)

    def myNextAction(self, data=None):
        return NAV_FORWARD

    def myPrevAction(self, data=None):
        return NAV_BACK

    def drawImpl(self):
        """
        All screen drawing code goes here. Don't draw the buttons as well, this
        is already done for you.
        """
        self.screenGrid = snack.Grid(1, 1)
        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                 width=self.gridWidth),
                                 col=0, row=0)

    def validate(self):
        """Validation code goes here. Activated when 'Next' button is pressed."""
        return True, 'Success'

    def formAction(self):
        """Any action other than validation that takes place after the
           'Next button is pressed.
        """
        self.add()

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
