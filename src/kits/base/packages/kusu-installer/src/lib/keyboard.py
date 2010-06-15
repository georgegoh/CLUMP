#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Keyboard Selection Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.

import snack
from gettext import gettext as _
from kusu.util import profile
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
import kusu.util.log as kusulog
from screen import InstallerScreen
from kusu.installer.keyboards import kbMap, kbDefault

kl = kusulog.getKusuLog('installer.keyboard')

def getKbMap():
    return kbMap

class KeyboardSelectionScreen(InstallerScreen, profile.PersistentProfile):
    """This screen asks for keyboard."""
    name = _('Keyboard')
    profile = 'Keyboard'
    msg = _('Please choose your keyboard:')
    buttons = []

    def __init__(self, kiprofile):
        InstallerScreen.__init__(self, kiprofile=kiprofile)
        profile.PersistentProfile.__init__(self, kiprofile)        

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 2)
        
        instruction = snack.Label(self.msg)
        self.screenGrid.setField(instruction, col=0, row=0)
        self.listbox = snack.Listbox(8, scroll=1, returnExit=1)
        self.kbMap = getKbMap()
        keyboardList = self.kbMap.keys()
        keyboardList.sort()
        for name in keyboardList:
            self.listbox.append(name, self.kbMap[name])

        if not self.kiprofile.has_key(self.profile): self.setDefaults()
        self.listbox.setCurrent(self.kiprofile[self.profile])

        self.screenGrid.setField(self.listbox, col=0, row=1,
                                 padding=(0,1,0,-1))

    def setDefaults(self):
        self.kiprofile[self.profile] = kbDefault

    def validate(self):
        errList = []

        if errList:
            errMsg = _('Please correct the following errors:')
            for i, string in enumerate(errList):
                errMsg = errMsg + '\n\n' + str(i+1) + '. ' + string
            return False, errMsg
        else:
            return True, ''

    def formAction(self):
        """
        Store the keyboard settings.
        """

        self.kiprofile[self.profile] = self.listbox.current()

    def rollback(self):
        self.formAction()

    def executeCallback(self, obj):
        if obj is self.listbox:
            return True
        return False

    def save(self, db, profile):
        newag = db.AppGlobals(kname=self.profile, kvalue=profile)
        newag.save()
        db.flush()

