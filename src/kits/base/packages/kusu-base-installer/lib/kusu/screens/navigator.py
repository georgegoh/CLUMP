#!/usr/bin/env python
#
# Kusu snack screens Navigator Framework.
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

"""This module is the backbone of the Text Installer Framework. It performs the 
   presentation, navigation,and data validation tasks."""

import sys
import logging
import snack
import gettext
import os
import time
from kusu.app import KusuApp

class PlatformScreen(snack.SnackScreen, KusuApp):
    """Represents the display.
    
    Inherits SnackScreen to display a custom help line at the foot of the screen.

    """
    def __init__(self, title, helpLine='Copyright(C) 2007 Platform Computing Inc.\t\t' + \
                                'Press F12 to quit'):
        KusuApp.__init__(self)
        snack.SnackScreen.__init__(self)
        snack.SnackScreen.popHelpLine(self)
        snack.SnackScreen.pushHelpLine(self, helpLine)

    def finish(self):
        snack.SnackScreen.popHelpLine(self)
        snack.SnackScreen.finish(self)

NAV_NOTHING = -1
NAV_FORWARD = 0
NAV_BACK = 1
NAV_QUIT = 2

class Navigator(object, KusuApp):
    """Framework for displaying installation steps and screens.

    The Navigator class takes a screenFactory object, and displays the
    screens in the order described in the screenFactory.

    """
    mainScreen = None
    sidebarWidth = 22
    currentStep = 0
    timerActivated = False

    def __getattr__(self, name):
        if name == 'currentScreen':
            return self.screens[self.currentStep]
        raise AttributeError, "%s instance has no attribute '%s'" % \
                              (self.__class__, name)

    def popupProgress(self, title, msg):
        return ProgressDialogWindow(self.mainScreen, title, msg)
        
    def popupMsg(self, title, msg):
        """Show a popup dialog with a given title and message."""
        msgbox = snack.GridForm(self.mainScreen, title, 1,2)
        text = snack.TextboxReflowed(30, msg)
        msgbox.add(text, 0,0)
        msgbox.add(snack.Button(self._('ok_button')), 0,1)
        return msgbox.runPopup()

    def popupStatus(self, title, msg, timeout):
	""" Show a status dialog that disappears after a timeout."""
	msgbox = snack.GridForm(self.mainScreen, title, 1,1)
	text = snack.TextboxReflowed(30, msg)
	msgbox.add(text,0, 0)
	msgbox.draw()
	self.mainScreen.refresh()
        if timeout >= 0:
	    time.sleep(timeout)
	    self.mainScreen.popWindow()
	
    def popupDialogBox(self, title, msg, buttonList):
	""" Show a popup dialog box and handle return a value for each button pressed. """
	msgbox = snack.ButtonChoiceWindow(self.mainScreen, title, msg, buttonList)
	return msgbox

    def popupInputBox(self, title, msg, prompts, cancelmode, buttonlist, width=40, entrywidth=20):
	""" Show a popup input dialog box and return the value typed in. """
	buttonPressed, entryValue = snack.EntryWindow(self.mainScreen, title, msg, prompts, allowCancel=cancelmode, width=40, entryWidth=20, buttons=buttonlist, help=None)
	return entryValue

    def __init__(self, screenFactory, screentitle, buttonspace=0, showTrail=False):
        """Constructor parameters:
              screenFactory - instance of the ScreenFactory class
              screenTitle - title of the Application Screen
              showTrail is a boolean to turn on or off the cookie trail display,
              which is shown as a sidebar.
	"""
	KusuApp.__init__(self)
	self.screenTitle = self._(screentitle)
        self.screenTimer = 0
	self.timerActivated = False
	self.quitButtonTitle = self._('finish_button')
        self.screens = screenFactory.createAllScreens()
	self.showTrail = showTrail
        self.buttonSpacing = buttonspace

    def isActiveTimer(self):
	return self.activeTimer

    def setActiveTimer(self, boolVal):
	""" If timer callback has been executed, check if we need to execute it again"""

	if boolVal not in (True, False): 
	   raise TypeError("Must specify boolean value")

	self.activeTimer = boolVal

    def endButtonTitle(self, title):
	self.quitButtonTitle = self._(title)

    def selectScreen(self, step):
        """Select(by number) the screen to be displayed. Will neither go below
           0, nor above the total number of screens available.
        """
        if step < 0:
            self.currentStep = 0
        elif step > len(self.screens) - 1:
            self.currentStep = len(self.screens) - 1
        else:
            self.currentStep=step

        # after we know which step we're on, display it(with or without trail).
        contentGrid = self.setupContentGrid()
        if self.showTrail:
            sidebarGrid = self.setupSidebarGrid()
            self.mainGrid = snack.Grid(2,1)
            self.mainGrid.setField(sidebarGrid, col=0, row=0, padding=(0,0,0,0))
            self.mainGrid.setField(contentGrid, col=1, row=0, padding=(0,0,0,1))
        else:
            self.mainGrid = snack.Grid(1,1)
            self.mainGrid.setField(contentGrid, col=0, row=0, padding=(0,0,0,0))

    def getCurrentScreen(self):
	""" Returns current screen """
	return self.screens[self.currentStep]

    def setupSidebarGrid(self):
        """Set up the sidebar that shows progress."""
        sidebarGrid = snack.Grid(1, len(self.screens))
        for i, screen in enumerate(self.screens):
            name = str(i) + '. ' + self._(screen.name)
            if i == self.currentStep:
                t = snack.Label(name.ljust(self.sidebarWidth-4))                
            else:
                t = snack.TextboxReflowed(width=self.sidebarWidth, text=name)
            sidebarGrid.setField(t, col=0, row=i)
        return sidebarGrid

    def setupContentGrid(self):
        """Set up the main content part of the screen."""
        contentGrid = snack.Grid(1, 2)
        currentScreen = self.screens[self.currentStep]
        currentScreen.draw(self.mainScreen, self)

	# Set up the Help text for each window.
	if currentScreen.helptext:
		self.mainScreen.pushHelpLine(currentScreen.helptext)

        contentGrid.setField(currentScreen.screenGrid, col=0,
                             row=0, padding=(0,0,0,0))
        buttons = []
        for key in self.screens[self.currentStep].buttons:
            buttons.append(self.screens[self.currentStep].buttonsDict[key])
        buttonPanel = self.setupButtonPanel(buttons)
        contentGrid.setField(buttonPanel, col=0, row=1, growx=1, growy=1,
                             padding=(0,0,0,2))
        return contentGrid

    def setupButtonPanel(self, buttons=[]):
        """Set up the buttons that navigate the screens."""
        currentScreen = self.screens[self.currentStep]
        self.prevButton = snack.Button(self._('previous_button'))
        if self.hasPrevScreen():
            buttons.insert(0, self.prevButton)
       
        if self.hasNextScreen():
            self.nextButton = snack.Button(self._('next_button'))
        else:
            if currentScreen.quitButtonDisabled == False:
                self.nextButton = snack.Button(self.quitButtonTitle)
            else:
                self.nextButton = None
            
        if self.nextButton:
            buttons.insert(0, self.nextButton)

        buttonGrid = snack.Grid(len(buttons), 1)
        for i, button in enumerate(buttons):
            buttonGrid.setField(button, col=i, row=0, padding=(0,0,self.buttonSpacing,0))
        return buttonGrid

    def hasNextScreen(self):
        """Is there another screen beyond the current displayed?"""
        return self.currentStep is not (len(self.screens) - 1)

    def disableBackButton(self):
	currentScreen = self.screens[self.currentStep]
	currentScreen.backButtonDisabled = True

    def disableQuitButton(self):
        currentScreen = self.screens[self.currentStep]
        currentScreen.quitButtonDisabled = True

    def hasPrevScreen(self):
        """Is there a screen before the current displayed?"""
        currentScreen = self.screens[self.currentStep]
        previousScreen = self.screens[self.currentStep - 1]
        if currentScreen.backButtonDisabled or self.currentStep == 0:
            return False
        elif previousScreen.isCommitment:
            return False
        else:
            return True

    def run(self):
        loop=True
        self.mainScreen = PlatformScreen(self.screenTitle)
        self.selectScreen(0)
        while(loop):
            form = self.draw()
            result = self.startEventLoop(form)
            if result is NAV_FORWARD:
                valid, msg = self.currentScreen.validate()
                if not valid:
                    snack.ButtonChoiceWindow(self.mainScreen, 
                                             self._('Validation Failed'), msg,
                                             buttons=[self._('ok_button')])
                    continue
                self.currentScreen.formAction()
                self.mainScreen.popWindow()
                self.mainScreen.finish()
                if self.hasNextScreen():                
                    self.mainScreen = PlatformScreen(self.screenTitle)
                    self.selectScreen(self.currentStep+1)
                    loop=True
                else:
		    self.screens[self.currentStep].hotkeyCallback()
                    loop=False
            elif result is NAV_BACK:
                self.mainScreen.finish()
                self.mainScreen = PlatformScreen(self.screenTitle)
                self.selectScreen(self.currentStep-1)
                loop=True
            elif result is NAV_NOTHING:
                self.mainScreen.finish()
                self.mainScreen = PlatformScreen(self.screenTitle)
                self.selectScreen(self.currentStep)
                loop=True
            elif result is NAV_QUIT:
                self.mainScreen.popWindow()
                self.mainScreen.finish()
                loop=False
            else:
                self.mainScreen.popWindow()
                self.mainScreen.finish()
                loop=False

    def draw(self):
	self.mainScreen.drawRootText(0, 0, self.screenTitle)
	currentScreen = self.screens[self.currentStep]
	self.mainScreen.gridWrappedWindow(self.mainGrid, self._(currentScreen.title))
        form = snack.Form(self._("This is the help statement"))
        form.add(self.mainGrid)
        return form

    def setScreenTimer(self, timerValue):
	self.screenTimer = timerValue

    def startEventLoop(self, form):     
        form.addHotKey("F12")
	form.setTimer(self.screenTimer)

        while True:
            result = form.run()
	    if result is "TIMER":
		timercallback_result = self.screens[self.currentStep].timerCallback()
            if result is "F12":
		hotkeycallback_result = self.screens[self.currentStep].hotkeyCallback()
                #return NAV_QUIT
            if result is self.nextButton:
                return NAV_FORWARD
            if result is self.prevButton:
                return NAV_BACK
            callback_result = self.screens[self.currentStep].eventCallback(result)
            if callback_result is True:
                return NAV_FORWARD
            elif callback_result is NAV_NOTHING:
                return NAV_NOTHING
