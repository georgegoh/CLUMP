#!/usr/bin/env python
# $Id$
#
# Kusu snack screens Navigator Framework.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
"""This module is the backbone of the TUI Framework. It performs the 
   presentation, navigation,and data validation tasks."""
__version__ = "$Revision: 242 $"

import os
import sys
import time
import snack
from kusu.core.app import KusuApp
from kusu.util.log import Logger


class PlatformScreen(snack.SnackScreen, KusuApp):
    """Represents the display.
    
    Inherits SnackScreen to display a custom help line at the foot of the screen.

    """
    logger = None
    instance_cnt = 0

    def __init__(self, title):
        snack.SnackScreen.__init__(self)
        KusuApp.__init__(self)
        self.logger = Logger()
        helpLine=self._('Copyright(C) 2007 Platform Computing Inc.\t\t' + \
                        'Press F12 to quit')
        snack.SnackScreen.pushHelpLine(self, helpLine)
        self.instance_cnt = self.instance_cnt + 1

    def finish(self):
        self.instance_cnt = self.instance_cnt - 1
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

       Hidden attribute - currentScreen
    """
    mainScreen = None
    sidebarWidth = 22
    currentStep = 0
    timerActivated = False
    logger = None

    def __getattr__(self, name):
        if name == 'currentScreen':
            return self.screens[self.currentStep]
        raise AttributeError, "%s instance has no attribute '%s'" % \
                              (self.__class__, name)

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

    def popupMsg(self, title, msg):
        """Show a popup dialog with a given title and message."""
        snack.ButtonChoiceWindow(self.mainScreen, title, msg,
                                 buttons=[self._('Ok')])

    def __init__(self, screenFactory, screenTitle, showTrail=False):
        """Constructor parameters:
              screenFactory - instance of the ScreenFactory class
              screenTitle - title of the Application Screen
              showTrail is a boolean to turn on or off the cookie trail display,
              which is shown as a sidebar.
        """
        KusuApp.__init__(self)
        self.logger = Logger()
        self.screenTitle = screenTitle
        self.timerActivated = False
        self.quitButtonTitle = self._('Finish')
        self.screens = screenFactory.createAllScreens()
        self.showTrail = showTrail


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


    def setupSidebarGrid(self):
        """Set up the sidebar that shows progress."""
        sidebarGrid = snack.Grid(1, len(self.screens))
        for i, screen in enumerate(self.screens):
            name = str(i) + '. ' + screen.name
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
        try:
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
                                                 buttons=[self._('Ok')])
                        continue
                    self.currentScreen.formAction()
                    self.mainScreen.popWindow()
                    self.mainScreen.finish()
                    self.mainScreen = PlatformScreen(self.screenTitle)
                    if self.hasNextScreen():                
                        self.selectScreen(self.currentStep+1)
                        loop=True
                    else:
                        loop=False
                elif result is NAV_BACK:
                    self.logger.debug('Back navigation from ' + self.currentScreen.name + ' number: ' + str(self.currentStep))
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
                    return False
                else:
                    self.mainScreen.popWindow()
                    self.mainScreen.finish()
                    loop=False
                    return None
        except Exception, e:
            import traceback
            tb = traceback.format_exc()
            self.popupMsg(self._('Unresolved exception'), tb)
            exception_log = open('/tmp/kusu/exception.dump', 'w')
            exception_log.write(tb)
            exception_log.close()
            self.mainScreen.popWindow()
            self.mainScreen.finish()
            sys.exit(1)
        return True

    def draw(self):
        self.mainScreen.drawRootText(0,0, self.screenTitle)
        currentScreen = self.screens[self.currentStep]
        self.mainScreen.gridWrappedWindow(self.mainGrid, currentScreen.name)
        form = snack.Form(self._("This is the help statement"))
        form.add(self.mainGrid)
        return form

    def startEventLoop(self, form):     
        form.addHotKey("F12")
        while True:
            result = form.run()
            if result is "F12":
                return NAV_QUIT
            if result is self.nextButton:
                return NAV_FORWARD
            if result is self.prevButton:
                return NAV_BACK
            callback_result = self.screens[self.currentStep].eventCallback(result)
            if callback_result is True:
                return NAV_FORWARD
            elif callback_result is NAV_NOTHING:
                return NAV_NOTHING
