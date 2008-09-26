#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Welcome Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
import snack
import subprocess
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.util.errors import *
from screen import InstallerScreen
from util import isDiskOrderAmbiguous, remarkMBRs
from kusu.partitiontool import DiskProfile

class WelcomeScreen(InstallerScreen):
    """This is the welcome screen."""
    name = _('Welcome')
    context = 'Welcome'
    msg = _('Welcome to the Kusu %s installation program. In the ' + \
          'following screens, you will be presented with questions ' + \
          'that will help you configure your new Kusu %s cluster.\n\n' + \
          'If you do not wish to continue at any point, please press ' + \
          'the F12 key. Otherwise, press Next to continue.') % ('${VERSION_STR}', '${VERSION_STR}')
    buttons = []
    dupMBR_prompt = True
    fix_dupMBR = True

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 1)
        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0)
        self.prechecks()

    def prechecks(self):
        dp = DiskProfile(fresh=False, probe_fstab=False)
        if not dp.disk_dict:
            raise NoDisksFoundError, 'This system cannot be set up because ' + \
                      'no disks could be found. Please check your system ' + \
                      'hardware to make sure that you have installed your ' + \
                      'disks correctly.'
        if self.dupMBR_prompt and isDiskOrderAmbiguous(dp):
            if self.fix_dupMBR:
                msg = 'The installer cannot automatically determine the first '
                msg += 'disk that this system boots from due to duplicate MBR '
                msg += 'signatures on some disks.\n\n'
                msg += 'To proceed, Kusu needs to make changes to the MBR signature '
                msg += 'of the affected disks and reboot. On reboot, the installer '
                msg += 'will then be able to determine which disk the system boots'
                msg += 'from.\n\n'
                msg += 'Please click "OK" to proceed, or power off now to stop the '
                msg += 'installation'
                self.selector.popupMsg('Cannot determine the first disk', msg,60)
                remarkMBRs(dp)
                subprocess.call(['reboot'])
            else:
                msg = 'The installer cannot automatically determine the first '
                msg += 'disk that this system boots from due to duplicate MBR '
                msg += 'signatures on some disks.\n\n'
                msg += 'Please refer to the installation guide for more information.'
                self.selector.popupDialogBox('Cannot determine the first disk', msg, ['Reboot'])
                subprocess.call(['reboot'])
