#!/usr/bin/env python
# $Id: tzselect.py 237 2007-04-05 08:57:10Z ggoh $
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

class TZSelectionScreen(screenfactory.BaseScreen):
    """This screen asks for timezone."""
    name = _('Time zone')
    context = 'Time zone'
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
        value = self.database.get(self.context, 'UTC')
        # by default checkbox is false, but if there's a stored value, use it.
        if not value: pass
        elif value[0] == 'True': self.utc.setValue('*')

        self.listbox = snack.Listbox(5, scroll=1, returnExit=1)
        self.getTZ()
        tzList = self.tz_dict.keys()
        tzList.sort()
        for name in tzList:
            self.listbox.append(name, name)
        value = self.database.get(self.context, 'Zone')
        if not value: self.listbox.setCurrent('America/New_York')
        else: self.listbox.setCurrent(value[0])

        entryWidth = 22
        value = self.database.get(self.context, 'NTP Server')
        if not value: value = 'pool.ntp.org'
        else: value = value[0]
        self.ntp = kusuwidgets.LabelledEntry(labelTxt=_('NTP Server '),
                                             width=entryWidth,
                                             text=value)

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
        tz = self.listbox.current()
        if self.utc.value():
            self.database.put(self.context, 'UTC', 'True')
        else:
            self.database.put(self.context, 'UTC', 'False')
        self.database.put(self.context, 'Zone', tz)
        self.database.put(self.context, 'NTP Server', self.ntp.value())

    def executeCallback(self, obj):
        if obj is self.listbox:
            return True
        return False
