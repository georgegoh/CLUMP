#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Language Selection Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.

import os
import snack
import gettext
from gettext import gettext as _
from kusu.util import profile
from kusu.ui.text import kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
import kusu.util.log as kusulog
from screen import InstallerScreen
from kusu.installer.languages import langMap, langDefault

kl = kusulog.getKusuLog('installer.language')

def getLangMap():
    return langMap
 
class LanguageSelectionScreen(InstallerScreen, profile.PersistentProfile):
    """This screen asks for language."""
    name = _('Language')
    profile = 'Language'
    msg = _('Please choose your language for installation:')
    buttons = []

    def __init__(self, kiprofile):
        InstallerScreen.__init__(self, kiprofile=kiprofile)
        profile.PersistentProfile.__init__(self, kiprofile)        
        self.langMap = getLangMap()

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 2)
        
        instruction = snack.Label(self.msg)
        self.screenGrid.setField(instruction, col=0, row=0)
        self.listbox = snack.Listbox(8, scroll=1, returnExit=1)

        languages = self.langMap.keys()
        languages.sort()
        for language in languages:
            self.listbox.append(language, self.langMap[language])

        if not self.kiprofile.has_key(self.profile): self.setDefaults()
        for k, v in self.langMap.iteritems():
            if k == self.kiprofile[self.profile]:
                self.kiprofile[self.profile] = k
        self.listbox.setCurrent(self.kiprofile[self.profile])

        self.screenGrid.setField(self.listbox, col=0, row=1,
                                 padding=(0,1,0,-1))

    def setDefaults(self):
        self.kiprofile[self.profile] = langDefault

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
        """This method is called by the framework to indicate an action is 
        required.
    
        Get selected language and set the subsequent screens to display that
        language.
        
        """

        langAttr = self.listbox.current()
        if langAttr not in ['en', 'en_US', 'en_GB']:
            try:
                t = gettext.translation('kusu', 'locale',
                                        languages=[langAttr])
                t.install()
            except IOError, e:
                snack.ButtonChoiceWindow(self.screen,
                                     'Cannot display language.',
                                     'Selected language cannot be shown' + \
                                     ' on this display. This installation ' + \
                                     'will proceed in English.', buttons=['Ok'])

        self.kiprofile[self.profile] = langAttr

    def rollback(self):
        langAttr = self.listbox.current()
        self.kiprofile[self.profile] = langAttr

    def executeCallback(self, obj):
        if obj is self.listbox:
            return True
        return False

    def save(self, db, profile):
        newag = db.AppGlobals(kname=self.profile, kvalue=profile)
        newag.save()
        db.flush()
