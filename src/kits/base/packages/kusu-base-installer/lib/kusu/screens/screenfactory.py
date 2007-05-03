#!/usr/bin/env python
#
# Kusu Text Installer Screen Factory.
#
# Copyright (C) 2007 Platform Computing Corporation

# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Author: George Goh <ggoh@platform.com>

"""This module contains the abstract classes BaseScreen and ScreenFactory, that
   users of the framework must subclass in order to use the Text Installer
   Framework."""
__version__ = "$Revision$"

import snack
import kusuwidgets
from gettext import gettext as _

NAV_NOTHING = -1
NAV_FORWARD = 0
NAV_BACK = 1
NAV_QUIT = 2

class BaseScreen:
    """Abstract base class for screens.
    
    This class is an abstract base class for other Screen classes to inherit.
    Child classes must implement a draw() method that defines what is in the
    screen.
    
    """
    name = "Base class"
    msg = 'This is the base class.'
    gridWidth = 0
    buttons = []
    buttonsDict = {} # Will be generated on init.
    backButtonDisabled = False
    dbconnection = None
    screen = None

    def setCallbacks(self):
        """(Abstract)

	Children should implement this if there are any buttons that
        require callbacks.

        """

    def drawImpl(self):
        """(Abstract)
        
        Children implement this method to draw their required widgets onscreen.
        Don't draw the buttons as well, this is already done for you.
        
        """

    def draw(self, screen, selector):
        """Template pattern method for drawing a screen

        Take in the caller's screen object. All children of BaseScreen should
        have access to it.

        """
        self.screen=screen
        self.selector=selector
        self.setCallbacks()
       	self.drawImpl()

    def validate(self):
        """(Abstract) Validation checks(if any) for user inputs should be here.

        validate() is called by the framework after the 'Next/Finish' button is
        pressed on the UI.
                
        """
        return True, 'Success'

    def formAction(self):
        """(Abstract)
        
        This method is called by the framework when the 'Next' or 'Finish'
        button is pressed.
        
        """

    def __init__(self, database, kusuapp, gridWidth=45):
	# Database instance of an KusuDB
        self.db = database
	self.kusuApp = kusuapp
        self.gridWidth = gridWidth
        for button in self.buttons:
            self.buttonsDict[button] = kusuwidgets.Button(button)

    def eventCallback(self, obj):
        """Template method for handling events(buttons or otherwise)."""
        buttonSuccess = self.executeCallbackForButton(obj)
        callbackSuccess = self.executeCallback(obj)
        if buttonSuccess == NAV_NOTHING or callbackSuccess == NAV_NOTHING:
            return NAV_NOTHING
        return buttonSuccess or callbackSuccess

    def executeCallbackForButton(self, button):
        """Callback lookup and activation for buttons."""
        for key in self.buttons:
            if button is self.buttonsDict[key]:
                if button.activateCallback_() == NAV_NOTHING:
                    return NAV_NOTHING
                return True
        return False

    def executeCallback(self, obj):
        """(Abstract) Callbacks for objects other than buttons.

        Returns:
            True if callback was handled.
            False if callback was not handled.
        """

class ScreenFactory:
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
