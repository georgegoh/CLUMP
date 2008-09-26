#!/usr/bin/env python
# $Id: screenfactory.py 476 2008-01-25 12:36:55Z hirwan $
#
# Kusu Text Installer Screen Factory.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
"""This module contains the abstract classes BaseScreen and ScreenFactory, that
   users of the framework must subclass in order to use the Text Installer
   Framework."""

import snack
import kusuwidgets
from navigator import NAV_QUIT, NAV_FORWARD, NAV_BACK, NAV_NOTHING, NAV_FORWARD_NO_VALIDATION

class BaseScreen(object):
    """Abstract base class for screens.
    
    This class is an abstract base class for other Screen classes to inherit.
    Child classes must implement a draw() method that defines what is in the
    screen.
    
    """
    name = 'Base class'
    context = 'No Context'
    msg = 'This is the base class.'
    gridWidth = 0
    buttons = []
    buttonsDict = None # will be generated on init.
    hotkeysDict = None
    backButtonDisabled = False
    isCommitment = False # if true, then this will be the point of no return.
    screen = None

    profile = 'No Profile'

    def __init__(self, gridWidth=45):
        self.gridWidth = gridWidth
        self.buttonsDict = {}
        for button in self.buttons:
            self.buttonsDict[button] = kusuwidgets.Button(button)

    def setHotKeys(self):
        pass

    def setCallbacks(self): # abstract
        """Children should implement this if there are any buttons that
           require callbacks.
        """
        pass # this statement may be replaced by raising a 'NotImplemented' exception.

    def drawImpl(self):
        """(Abstract)
        
        Children implement this method to draw their required widgets onscreen.
        Don't draw the buttons as well, this is already done for you.
        
        """
        pass # this statement may be replaced by raising a 'NotImplemented' exception.

    def draw(self, screen, selector):
        """Template pattern method for drawing a screen

        Take in the caller's screen object. All children of BaseScreen should
        have access to it.

        """
        self.screen=screen
        self.selector=selector
        self.setCallbacks()
        self.setHotKeys()
        self.drawImpl()

    def validate(self):
        """(Abstract) Validation checks(if any) for user inputs should be here.

        validate() is called by the framework after the 'Next/Finish' button is
        pressed on the UI.
                
        """
        return True, 'Success'

    def rollback(self):
        """(Abstract) Rollback method actions called to rollback changes made in this screen.

        rollback() is called by the framework after the 'Prev' button is pressed
        on the UI.
        """
        pass

    def formAction(self):
        """(Abstract)
        
        This method is called by the framework when the 'Next' or 'Finish'
        button is pressed.
        
        """
        pass

    def eventCallback(self, obj):
        """Template method for handling events(buttons or otherwise)."""
        buttonSuccess = self.executeCallbackForButton(obj)
        callbackSuccess = self.executeCallback(obj)
        if buttonSuccess == NAV_NOTHING or callbackSuccess == NAV_NOTHING:
            return NAV_NOTHING
        if buttonSuccess == NAV_FORWARD or callbackSuccess == NAV_FORWARD:
            return NAV_FORWARD
        if buttonSuccess == NAV_FORWARD_NO_VALIDATION or \
           callbackSuccess == NAV_FORWARD_NO_VALIDATION:
            return NAV_FORWARD_NO_VALIDATION
        return buttonSuccess or callbackSuccess

    def executeCallbackForButton(self, button):
        """Callback lookup and activation for buttons."""
        for key in self.buttons:
            if button is self.buttonsDict[key]:
                result = button.activateCallback_()
                if result in [NAV_QUIT, NAV_FORWARD, NAV_BACK,\
                              NAV_NOTHING, NAV_FORWARD_NO_VALIDATION]:
                    return result
                return True
        return False

    def executeCallback(self, obj):
        """(Abstract) Callbacks for objects other than buttons.

        Returns:
            True if callback was handled.
            False if callback was not handled.
        """
        pass # this statement may be replaced by raising a 'NotImplemented' exception.


class ScreenFactory(object):
    """Contains a number of screens used/navigated by the KusuInstaller class.
    
    The ScreenFactory is a base class for passing on to the 
    KusuInstaller class.
    
    Children must have the ScreenFactory.screens variable defined. See
    screenfactory_sample.py.

    """
    name='Base name'

    def createAllScreens(width=45):
        screenList = []
        for screen in ScreenFactory.screens:
            screenList.append(screen)
        return screenList
    createAllScreens = staticmethod(createAllScreens)
