#!/usr/bin/env python
# $Id$
#
# Kusu Text UI Screen Factory.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.ui.text.screenfactory import BaseScreen,ScreenFactory
import kusu.ngedit.ui.text.USXkusuwidgets
from kusu.ui.text.navigator import NAV_NOTHING,NAV_FORWARD,NAV_BACK,NAV_QUIT

class USXBaseScreen(BaseScreen):
    """Abstract base class for screens.
    This class is an abstract base class for other Screen classes to inherit.
    Child classes must implement a draw() method that defines what is in the
    screen.
    """
    dbSelected = 'MySQL'

    def __init__(self, database, kusuApp=None, gridWidth=45):
        self.buttonsDict = {}
        self.hotkeysDict = {}
        self.database = database
        self.kusuApp = kusuApp
        self.gridWidth = gridWidth
        self.screenTimer = None
        self.HelpLine = None

        #the base class should handle internationalization for all strings it introduces
        self.msg  = self.kusuApp._(self.msg)
        self.name = self.kusuApp._(self.name)
        self.context = self.kusuApp._(self.context)

        #create the dictionary of internationalized button instances
        for button in self.buttons:
            self.buttonsDict[button] = kusu.ui.text.USXkusuwidgets.USXButton(self.kusuApp._(button))


    def draw(self, screen, selector):
        """Template pattern method for drawing a screen

        Take in the caller's screen object. All children of BaseScreen should
        have access to it.

        """
        self.screen=screen
        self.selector=selector
        #if HelpLine is set - push it to the screen
        if type(self.HelpLine) == type(''):
            self.screen.pushHelpLine(self.HelpLine)
        self.setCallbacks()
        self.drawImpl()

    def setHelpLine(self,text):
            self.HelpLine = text


    def timerCallback(self):
        ''' timerCallback - to be implemented by child screen classes.
            Returns
                True if callback was handled.
                False if callback was not handled.
        '''
        return True

    def addHotKeys(self, form):
        for key in self.hotkeysDict.keys():
            form.addHotKey(key)
            
    def executeHotKeyCallback(self,hk):
        if hk in self.hotkeysDict.keys():
            f = self.hotkeysDict[hk]
            if f:
                return f()
            return True #hotkey in dict but no callback method assigned
        return False #captured event not a hotkey event

    def setScreenTimer(self,msec):
        if msec and msec > 0:
            self.screenTimer = msec

    def addTimer(self,form):
        if self.screenTimer:
            form.setTimer(self.screenTimer)

    def executeTimerCallback(self,obj):
        if obj == "TIMER":
            return self.timerCallback()
        return False #not a timer event

    def executeCallback(self,obj):
        ''' Callbacks for objects other than buttons. 
            Returns:
                True if callback was handled.
                False if callback was not handled.
        '''
        hkSuccess = self.executeHotKeyCallback(obj)
        tmSuccess = self.executeTimerCallback(obj)
        return hkSuccess or tmSuccess

    def executeCallbackForButton(self, button):
        """Callback lookup and activation for buttons."""
        for key in self.buttons:
            if button is self.buttonsDict[key]:
                result = button.activateCallback_()
                if result in (NAV_QUIT,NAV_FORWARD,NAV_BACK,NAV_NOTHING):
                    return result
                return True #button callback handled, non-nav return result
        return False
