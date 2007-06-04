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
NAV_NOTHING = -1
NAV_FORWARD = -2
NAV_BACK = 1
NAV_QUIT = 2

import os
import sys
import time
import snack
from kusu.core.app import KusuApp
from kusu.util.log import Logger
from path import path
from kusuwidgets import *
from kusu.util.errors import *

class PlatformScreen(snack.SnackScreen, KusuApp):
    """Represents the display.
    
    Inherits SnackScreen to display a custom help line at the foot of the screen.

    """
    logger = None

    def __init__(self, title):
        snack.SnackScreen.__init__(self)
        KusuApp.__init__(self)
        self.logger = Logger()
        helpLine=self._('Copyright(C) 2007 Platform Computing Inc.\t\t' + \
                        'Press F12 to quit')
        snack.SnackScreen.popHelpLine(self)
        snack.SnackScreen.pushHelpLine(self, helpLine)

    def finish(self):
        snack.SnackScreen.popHelpLine(self)
        snack.SnackScreen.finish(self)


class Navigator(object, KusuApp):
    """Framework for displaying installation steps and screens.

       The Navigator class takes a screenFactory object, and displays the
       screens in the order described in the screenFactory.
    """
    mainScreen = None
    sidebarWidth = 22
    currentStep = 0
    timerActivated = False
    logger = None
    currentScreen = property(lambda self : self.screens[self.currentStep],
                             None,
                             doc='The screen object that is currently displayed.')

    def popupProgress(self, title, msg):
        return ProgressDialogWindow(self.mainScreen, title, msg)

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

    def popupYesNo(self, title, msg):
        """Show a popup dialog with a yes/no answer. Return True on yes, False on No."""
        buttons = [self._('Yes'), self._('No')]
        result = self.popupDialogBox(title, msg, buttons)
        if result == buttons[0].lower(): return True
        else: return False

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
        self.currentScreen.draw(self.mainScreen, self)
        contentGrid.setField(self.currentScreen.screenGrid, col=0,
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
        buttons.insert(0, self.nextButton)

        buttonGrid = snack.Grid(len(buttons), 1)
        for i, button in enumerate(buttons):
            buttonGrid.setField(button, col=i, row=0, padding=(0,0,0,0))
        return buttonGrid


    def hasNextScreen(self):
        """Is there another screen beyond the current displayed?"""
        return self.currentStep is not (len(self.screens) - 1)


    def hasPrevScreen(self):
        """Is there a screen before the current displayed?"""
        previousScreen = self.screens[self.currentStep - 1]

        if self.currentScreen.backButtonDisabled or self.currentStep == 0:
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
                                                 self._('Validation Failed'),
                                                 msg,
                                                 buttons=[self._('Ok')])
                        continue
                    self.currentScreen.formAction()
                    self.mainScreen.popWindow()
                    self.mainScreen.finish()
                    if self.hasNextScreen():                
                        self.mainScreen = PlatformScreen(self.screenTitle)
                        self.selectScreen(self.currentStep+1)
                        loop=True
                    else:
                        loop=False
                elif result is NAV_BACK:
                    self.logger.debug('Back navigation from ' + \
                                      self.currentScreen.name + \
                                      ' number: ' + str(self.currentStep))
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
        except UserExitError, e:
            self.mainScreen.popWindow()
            self.mainScreen.finish()
            return False
        except KusuError, e:
            msg = str(e)
            import traceback
            tb = traceback.format_exc()
            msg = msg + '\n' + tb
            self.popupMsg(self.currentScreen.name, str(e))
            self.mainScreen.finish()
            raise e
        except Exception, e:
            import traceback
            tb = traceback.format_exc()
            kusu_tmp = os.environ.get('KUSU_TMP', None)
           
            if not kusu_tmp: 
                kusu_tmp = '/tmp/kusu'

            exception_log = open(path(kusu_tmp) / 'exception.dump', 'w')
            exception_log.write(tb)
            exception_log.close()
            self.popupMsg(self._('Unresolved exception'), tb)
            self.mainScreen.popWindow()
            self.mainScreen.finish()
            raise e
        return True

    def draw(self):
        self.mainScreen.drawRootText(0,0, self.screenTitle)
        self.mainScreen.gridWrappedWindow(self.mainGrid, self.currentScreen.name)
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
