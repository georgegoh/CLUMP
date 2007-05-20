#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Kits Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.

import snack
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
import kusu.util.log as kusulog

kl = kusulog.getKusuLog('installer.kits')

NAV_NOTHING = -1

class KitsScreen(screenfactory.BaseScreen):
    """Collects kits information."""
    name = _('Kits')
    context = 'Kits'
    profile = context
    msg = _('Please enter a Fedora 6 URL:')
    buttons = [_('Clear All')]

    def setCallbacks(self):
        """
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        """

        self.buttonsDict[_('Clear All')].setCallback_(self.clearAllFields)

    def clearAllFields(self):
        self.kiprofile[self.profile]['fedora_url'] = ''
        return NAV_NOTHING

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 2)
        entryWidth = 33

        self.url = kusuwidgets.LabelledEntry(
                        labelTxt=_('URL ').rjust(4), 
                        width=entryWidth,
                        text=self.kiprofile[self.profile]['fedora_url'])

        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0, anchorLeft=1)
        self.screenGrid.setField(self.url, col=0, row=1,
                                 padding=(0,1,0,1), anchorLeft=1)

    def validate(self):
        return True, ''

    def formAction(self):
        """
        Store
        """

        self.kiprofile[self.profile]['fedora_url'] = self.url.value()

    def restoreProfileFromSQLCollection(db, context, kiprofile):
        """
        Reads data from SQLiteCollection db according to context and fills
        profile.

        Arguments:
        db -- an SQLiteCollection object ready to accept data
        context -- the context to use to access data in db and profile
        kiprofile -- the complete profile (a dictionary) which we fill in
        """

        fedora = db.get(context, 'FedoraURL')
        if not fedora:
            fedora = 'http://172.25.208.218/repo/fedora/6/i386/os/'
        else:
            fedora = fedora[0]

        kl.info('Read Fedora URL from DB: %s' % fedora)

        kiprofile[context]['fedora_url'] = fedora

        return True

    def saveProfileToSQLCollection(db, context, kiprofile):
        """
        Writes data from profile to SQLiteCollection db according to context.

        Arguments:
        db -- an SQLiteCollection object ready to accept data
        context -- the context to use to access data in db and profile
        kiprofile -- the profile (a dictionary) with data to commit
        """

        db.put(context, 'FedoraURL', kiprofile[context]['fedora_url'])
 
        kl.info('Wrote kits info to DB')

        return True

    dbFunctions = {'MySQL': (None, None),
                   'SQLite': (None, None),
                   'SQLColl': (restoreProfileFromSQLCollection,
                               saveProfileToSQLCollection)}
