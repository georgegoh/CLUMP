#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Timezone Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision: 237 $"

import __init__
#import logging
import snack
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
import kusu.util.log as kusulog

kl = kusulog.getKusuLog('installer.kits')

class TZSelectionScreen(screenfactory.BaseScreen):
    """This screen asks for timezone."""
    name = _('Time Zone')
    context = 'Timezone'
    profile = context
    msg = _('Please choose your time zone:')
    buttons = []
    tz_dict = {} # key=Location, value=[CC, Lat-long, Comments]

    def setCallbacks(self):
        """
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        """

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 4)
        
        instruction = snack.Label(self.msg)

        self.utc = snack.Checkbox(_('System uses UTC'))
        if self.kiprofile[self.profile]['utc']:
            self.utc.setValue('*')

        self.listbox = snack.Listbox(5, scroll=1, returnExit=1)
        self.getTZ()
        tzList = self.tz_dict.keys()
        tzList.sort()
        for name in tzList:
            self.listbox.append(name, name)
        self.listbox.setCurrent(self.kiprofile[self.profile]['zone'])

        entryWidth = 22
        self.ntp = kusuwidgets.LabelledEntry(labelTxt=_('NTP Server '),
                             width=entryWidth,
                             text=self.kiprofile[self.profile]['ntp_server'])

        self.screenGrid.setField(instruction, col=0, row=0, growx=1)
        self.screenGrid.setField(self.utc, col=0, row=1, growx=1, padding=(0,1,0,0))
        self.screenGrid.setField(self.listbox, col=0, row=2)
        self.screenGrid.setField(self.ntp, col=0, row=3, growx=1, padding=(0,1,0,-1))

    def getTZ(self):
        f = file('/usr/share/zoneinfo/zone.tab')
        line = f.readline()
        while line != '':
            if line.strip()[0] != '#':
                li = line.split('\t')
                if len(li) > 3:
                    self.tz_dict[li[2]] = [li[0], li[1], li[3]]
                else:
                    self.tz_dict[li[2]] = [li[0], li[1], '']
            line = f.readline()
        f.close()

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
        Put the values entered into the database.
        """

        self.kiprofile[self.profile]['zone'] = self.listbox.current()
        self.kiprofile[self.profile]['utc'] = bool(self.utc.value())
        self.kiprofile[self.profile]['ntp_server'] = self.ntp.value()

    def executeCallback(self, obj):
        if obj is self.listbox:
            return True
        return False

    def restoreProfileFromSQLCollection(db, context, kiprofile):
        """
        Reads data from SQLiteCollection db according to context and fills
        profile.

        Arguments:
        db -- an SQLiteCollection object ready to accept data
        context -- the context to use to access data in db and profile
        kiprofile -- the complete profile (a dictionary) which we fill in
        """

        profile = {}
        profile['utc'] = False
        profile['zone'] = 'America/New_York'
        profile['ntp_server'] = 'pool.ntp.org'

        utc = db.get(context, 'UTC')
        if utc and utc[0] == 'True':
            profile['utc'] = True

        zone = db.get(context, 'Zone')
        if zone:
            profile['zone'] = zone[0]

        ntp = db.get(context, 'NTP Server')
        if ntp:
            profile['ntp_server'] = ntp[0]

        kl.info('Read time zone info from DB')

        kiprofile[context] = profile

        return True

    def saveProfileToSQLCollection(db, context, kiprofile):
        """
        Writes data from profile to SQLiteCollection db according to context.

        Arguments:
        db -- an SQLiteCollection object ready to accept data
        context -- the context to use to access data in db and profile
        kiprofile -- the profile (a dictionary) with data to commit
        """

        profile = kiprofile[context]
        if profile['utc']:
            db.put(context, 'UTC', 'True')
        else:
            db.put(context, 'UTC', 'False')
        db.put(context, 'Zone', profile['zone'])
        db.put(context, 'NTP Server', profile['ntp_server'])

        kl.info('Wrote time zone info to DB')

        return True

    dbFunctions = {'MySQL': (None, None),
                   'SQLite': (None, None),
                   'SQLColl': (restoreProfileFromSQLCollection,
                               saveProfileToSQLCollection)}
