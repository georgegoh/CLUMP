import snack
from kusu.ui.text.USXscreenfactory import USXBaseScreen,ScreenFactory
from kusu.ui.text.USXnavigator import *
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB

class NGPlugin(USXBaseScreen):
    name= 'Base Installer Plugin Screen'
    msg = 'wigdets go here\n' +\
          'Level 2'
    buttons = ['next_button', 'prev_button']
    hotkeysDict = {}

    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.setHelpLine("Help for base-installer component's plugin screen")

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
        pass
