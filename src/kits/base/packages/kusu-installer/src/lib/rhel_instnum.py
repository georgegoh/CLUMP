#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer License Entry Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import snack
from gettext import gettext as _
from kusu.util import profile
from kusu.ui.text import kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
import kusu.util.log as kusulog
from screen import InstallerScreen
from kusu.ui.text.navigator import NAV_FORWARD_NO_VALIDATION
from path import path
import instnum

kl = kusulog.getKusuLog('installer.instnum')

class LicenseScreen(InstallerScreen, profile.PersistentProfile):
    name = _('Inst Number')
    profile = 'InstNum'
    msg = _('Please enter Red Hat Installation number')
    buttons = [_('Skip')]

    def __init__(self, kiprofile):
        InstallerScreen.__init__(self, kiprofile=kiprofile)
        profile.PersistentProfile.__init__(self, kiprofile)        

    def setCallbacks(self):
        """
        
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        
        """
        self.buttonsDict[_('Skip')].setCallback_(self.skip)

    def skip(self):
        kl.debug('Skipping')
        return NAV_FORWARD_NO_VALIDATION

    def drawImpl(self):
        
        if not self.kiprofile.has_key(self.profile): self.setDefaults()

        self.screenGrid = snack.Grid(1, 2)
        entryWidth = 20
        self.license = kusuwidgets.LabelledEntry(
                       labelTxt=_('Installation number ').rjust(26), 
                       width=entryWidth, text=self.kiprofile[self.profile])

        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0, anchorLeft=1)
        self.screenGrid.setField(self.license, col=0, row=1, anchorLeft=1,
                                 padding=(0,1,0,1))

    def validate(self):
        kl.debug('validate instnum')
        key = self.license.value()

        # Reference from anaconda, installclasses/rhel.py
        try:
            inum = instnum.InstNum(key)
        except:
            errMsg = _("Invalid installation number\n\n" \
                       "If you're unable to locate\n" \
                       "the Installation Number, consult\n" \
                       "http://www.redhat.com/apps/support/in.html.")
            return False, errMsg

        if inum:
            # make sure the base products match
            buildstamp = path('/.buildstamp')
            
            if buildstamp.exists():
                f = buildstamp.open()
                productPath = f.readlines()[3].strip()
                f.close()

                if inum.get_product_string().lower() != productPath.lower():
                    return False, _('Installation number incompatible with media')
    
        return True, ''

    def setDefaults(self):
        self.kiprofile[self.profile] = ''

    def formAction(self):
        """
        Store
        """

        self.kiprofile[self.profile] = self.license.value()

    def save(self, db, profile):
        newag = db.AppGlobals(kname=self.profile, kvalue=profile)
        newag.save()
        db.flush()
