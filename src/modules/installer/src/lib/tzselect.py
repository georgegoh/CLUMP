#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Timezone Setup Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import snack
from gettext import gettext as _
from kusu.util import profile
from path import path
from kusu.ui.text import kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
import kusu.util.log as kusulog
from screen import InstallerScreen

try:
    import subprocess
except:
    from popen5 import subprocess

kl = kusulog.getKusuLog('installer.kits')

class TZSelectionScreen(InstallerScreen, profile.PersistentProfile):
    """This screen asks for timezone."""
    name = _('Time Zone')
    profile = 'Timezone'
    msg = _('Please choose your time zone:')
    buttons = []
    tz_dict = {} # key=Location, value=[CC, Lat-long, Comments]

    def __init__(self, kiprofile):
        InstallerScreen.__init__(self, kiprofile=kiprofile)
        profile.PersistentProfile.__init__(self, kiprofile)        

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

    def setDefaults(self):
        self.kiprofile[self.profile] = {}
        self.kiprofile[self.profile]['utc'] = False
        self.kiprofile[self.profile]['ntp_server'] = 'pool.ntp.org'
        self.kiprofile[self.profile]['zone'] = 'Asia/Singapore'

    def getTZ(self):
        f = file('/usr/share/zoneinfo/zone.tab')
        line = f.readline()
        while line != '':
            if line.strip()[0] != '#':
                li = line.split('\t')
                if len(li) > 3:
                    self.tz_dict[li[2].strip()] = [li[0], li[1], li[3]]
                else:
                    self.tz_dict[li[2].strip()] = [li[0], li[1], '']
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
        Put the values entered into the kiprofile.
        """

        self.kiprofile[self.profile]['zone'] = self.listbox.current()
        self.kiprofile[self.profile]['utc'] = bool(self.utc.value())
        self.kiprofile[self.profile]['ntp_server'] = self.ntp.value()

        # now we set the system time to what we just selected
        tzfile = path('/usr/share/zoneinfo') / self.kiprofile[self.profile]['zone']
        tzfile.copy('/etc/localtime')

        hwclock_args = '--hctosys'
        if self.kiprofile[self.profile]['utc']:
            hwclock_args += ' -u'

        hwclockP = subprocess.Popen('hwclock %s' % hwclock_args, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        hwclockP.communicate()

    def executeCallback(self, obj):
        if obj is self.listbox:
            return True
        return False

    def save(self, db, profile):
        newag_zone = db.AppGlobals(kname=self.profile + '_zone',
                                   kvalue=profile['zone'])
        newag_zone.save()

        newag_utc = db.AppGlobals(kname=self.profile + '_utc',
                                  kvalue=profile['utc'])
        newag_utc.save()

        newag_ntp = db.AppGlobals(kname=self.profile + '_ntp_server',
                                  kvalue=profile['ntp_server'])
        newag_ntp.save()

        db.flush()
