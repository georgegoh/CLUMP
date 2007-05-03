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
__version__ = "$Revision: 155 $"

import sys
import logging
import snack
import gettext
import os
import time

class PlatformScreen(snack.SnackScreen):
    """Represents the display.
    
    Inherits SnackScreen to display a custom help line at the foot of the screen.

    """
    def __init__(self, title, helpLine='Copyright(C) 2007 Platform Computing Inc.\t\t' + \
                                'Press F12 to quit'):
        snack.SnackScreen.__init__(self)
        self.pushHelpLine(helpLine)

    def finish(self):
        self.popHelpLine()
        snack.SnackScreen.finish(self)

NAV_NOTHING = -1
NAV_FORWARD = 0
NAV_BACK = 1
NAV_QUIT = 2

class Navigator:
    """Framework for displaying installation steps and screens.

    The Navigator class takes a screenFactory object, and displays the
    screens in the order described in the screenFactory.

    """
    mainScreen = None
    sidebarWidth = 22

    def popupMsg(self, title, msg):
        """Show a popup dialog with a given title and message."""
        msgbox = snack.GridForm(self.mainScreen, title, 1,2)
        text = snack.TextboxReflowed(30, msg)
        msgbox.add(text, 0,0)
        msgbox.add(snack.Button('Ok'), 0,1)
        return msgbox.runPopup()

    def popupStatus(self, title, msg, timeout):
	""" Show a status dialog that disappears after a timeout."""
	msgbox = snack.GridForm(self.mainScreen, title, 1,1)
	text = snack.TextboxReflowed(30, msg)
	msgbox.add(text,0, 0)
	msgbox.draw()
	self.mainScreen.refresh()
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

    def __init__(self, screenFactory, screentitle, wizardmode=False):
	""" Constructor parameters:
	
	screentitle is title of the Application Screen
	wizardmode is the sidebar text displayed by default turned off for kusu applications.

	"""
	self._ = self.langinit()
	self.screenTitle = self._(screentitle)
	self.screenTimer = 0
	self.activeTimer = False
	self.quitButtonTitle = self._('finish_button')
        self.screens = screenFactory.createAllScreens()
	self.wizardMode = wizardmode

    def isActiveTimer(self):
	return self.activeTimer

    def setActiveTimer(self, boolVal):
	""" If timer callback has been executed, check if we need to execute it again"""

	if boolVal not in (True, False): 
	   raise TypeError("Must specify boolean value")

	self.activeTimer = boolVal

    def endButtonTitle(self, title):
	self.quitButtonTitle = self._(title)

    def langinit(self):
        """langinit - Initialize the Internationalization """
        langdomain = 'kusuapps'
        localedir  = ''

        # Locate the Internationalization stuff
        if os.path.exists('../locale'):
            localedir = '../locale'
        else:
            # Try the system path
            if os.path.exists('/usr/share/locale'):
                localedir = '/usr/share/locale'

        gettext.bindtextdomain(langdomain, localedir)
        gettext.textdomain(langdomain)
        self.gettext = gettext.gettext
        return self.gettext

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

	if self.wizardMode:	
           sidebarGrid = self.setupSidebarGrid()

        contentGrid = self.setupContentGrid()
        self.mainGrid = snack.Grid(2, 1)
        
        if self.wizardMode:
           self.mainGrid.setField(sidebarGrid, col=0, row=0, padding=(0,0,0,0))

        self.mainGrid.setField(contentGrid, col=1, row=0, padding=(0,0,0,1))

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
        contentGrid.setField(currentScreen.screenGrid, col=0,
                             row=0, padding=(0,0,0,0))
        buttons = []
        for key in self.screens[self.currentStep].buttons:
            buttons.append(self.screens[self.currentStep].buttonsDict[key])
        buttonPanel = self.setupButtonPanel(buttons)
        contentGrid.setField(buttonPanel, col=0, row=1, growx=1, growy=1,
                             padding=(0,0,0,0))
        return contentGrid

    def setupButtonPanel(self, buttons=[]):
        """Set up the buttons that navigate the screens."""
        self.prevButton = snack.Button(self._('Prev'))
        if self.hasPrevScreen():
            buttons.insert(0, self.prevButton)

        if self.hasNextScreen():
            self.nextButton = snack.Button(self._('Next'))
        else:
            self.nextButton = snack.Button(self.quitButtonTitle)
        buttons.append(self.nextButton)
        buttonGrid = snack.Grid(len(buttons), 1)
        for i, button in enumerate(buttons):
            buttonGrid.setField(button, col=i, row=0, padding=(0,0,0,0))
        return buttonGrid

    def hasNextScreen(self):
        """Is there another screen beyond the current displayed?"""
        return self.currentStep is not (len(self.screens) - 1)

    def disableBackButton(self):
	currentScreen = self.screens[self.currentStep]
	currentScreen.backButtonDisabled = True

    def hasPrevScreen(self):
        """Is there a screen before the current displayed?"""
        currentScreen = self.screens[self.currentStep]
        if currentScreen.backButtonDisabled or self.currentStep == 0:
            return False
        else:
            return True

    def run(self):
        loop=True
        self.selectScreen(0)
        while(loop):
            self.mainScreen = PlatformScreen(self.screenTitle)
            form = self.draw()
            result = self.startEventLoop(form)
            if result is NAV_FORWARD:
                currentScreen = self.screens[self.currentStep]
                valid, msg = currentScreen.validate()
                if not valid:
                    snack.ButtonChoiceWindow(self.mainScreen, 
                                             self._('Validation Failed'), msg,
                                             buttons=[self._('Ok')])
                    continue
                currentScreen.formAction()
                self.mainScreen.popWindow()
                self.mainScreen.finish()
                if self.hasNextScreen():                
                    self.selectScreen(self.currentStep+1)
                    loop=True
                else:
		    self.screens[self.currentStep].hotkeyCallback()
                    loop=False
            elif result is NAV_BACK:
                self.mainScreen.finish()
                self.selectScreen(self.currentStep-1)
                loop=True
            elif result is NAV_NOTHING:
                self.mainScreen.finish()
                self.selectScreen(self.currentStep)
                loop=True
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
