import snack
import time
import kusu.ui.text.navigator
from kusu.ui.text.navigator import NAV_QUIT,NAV_FORWARD, NAV_BACK, NAV_NOTHING

NAV_IGNORE = 3

class USXNavigator(kusu.ui.text.navigator.Navigator):
    """Framework for displaying installation steps and screens.

       The Navigator class takes a screenFactory object, and displays the
       screens in the order described in the screenFactory.
    """

    def setupContentGrid(self):
        """Set up the main content part of the screen."""
        contentGrid = snack.Grid(1, 2)
        self.currentScreen.draw(self.mainScreen, self)
        contentGrid.setField(self.currentScreen.screenGrid, col=0,
                             row=0, padding=(0,0,0,0))
        buttons = []
        for key in self.screens[self.currentStep].buttons:
            buttons.append(self.screens[self.currentStep].buttonsDict[key])
        buttonPanel = self.setupButtonPanel(buttons)
        contentGrid.setField(buttonPanel, col=0, row=1, growx=1, anchorLeft=1, #growy=1
                             padding=(0,1,0,0))
        return contentGrid


    def setupButtonPanel(self, buttons=[]):
        """Set up the buttons that navigate the screens."""

        #navigation buttons should be at the discretion of the child screens
        buttonGrid = snack.Grid(len(buttons), 1)
        for i, button in enumerate(buttons):
            buttonGrid.setField(button, col=i, row=0, padding=(0,0,0,0))
        return buttonGrid

    def startEventLoop(self, form):     
        self.screens[self.currentStep].addHotKeys(form)
        self.screens[self.currentStep].addTimer(form)
        while True:
            result = form.run()
            # eventloop callback hook
            callback_result = self.screens[self.currentStep].eventCallback(result)
            # process the result of callback handling
            if callback_result == NAV_IGNORE:
                continue
            if callback_result in (NAV_QUIT,NAV_FORWARD,NAV_BACK,NAV_NOTHING):
                return callback_result
            else:
                return NAV_NOTHING
