#!/usr/bin/env python
# $Id: clusterinfo.py 237 2007-04-05 08:57:10Z ggoh $
#
# Kusu Text Installer Cluster Info Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision: 237 $"

import logging
import snack
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT

NAV_NOTHING = -1

class ClusterInfoScreen(screenfactory.BaseScreen):
    """Collects info about the cluster."""
    name = _('Cluster Info')
    msg = _('Please enter the following information:')
    buttons = [_('Clear All')]

    def setCallbacks(self):
        """
        
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        
        """
        self.buttonsDict[_('Clear All')].setCallback_(self.clearAllFields)

    def clearAllFields(self):
        self.fqhn.setEntry('')
        self.clusterName.setEntry('')
        self.organisation.setEntry('')
        self.locality.setEntry('')
        self.state.setEntry('')
        self.country.setEntry('')
        self.contact.setEntry('')
        self.url.setEntry('')
        self.latlong.setEntry('')
        return NAV_NOTHING

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 10)
        entryWidth = 30
        value = self.database.get(self.name, 'FQHN')
        if not value: value = 'cluster.hpc.org'
        else: value = value[0]
        self.fqhn = kusuwidgets.LabelledEntry(
                        labelTxt=_('Fully-Qualified Host Name ').rjust(26), 
                        width=entryWidth, text=value)
        self.fqhn.addCheck(kusuwidgets.verifyFQDN)

        value = self.database.get(self.name, 'ClusterName')
        if not value: value = 'Our Cluster'
        else: value = value[0]
        self.clusterName = kusuwidgets.LabelledEntry(
                               labelTxt=_('Cluster Name ').rjust(26),
                               width=entryWidth, text=value)

        value = self.database.get(self.name, 'Organisation')
        if not value: value = 'OSGDC'
        else: value = value[0]
        self.organisation = kusuwidgets.LabelledEntry(
                                labelTxt=_('Organisation ').rjust(26),
                                width=entryWidth, text=value)

        value = self.database.get(self.name, 'Locality')
        if not value: value = 'Singapore'
        else: value = value[0]
        self.locality = kusuwidgets.LabelledEntry(
                            labelTxt=_('Locality ').rjust(26),
                            width=entryWidth, text=value)

        value = self.database.get(self.name, 'State')
        if not value: value = 'Singapore'
        else: value = value[0]
        self.state = kusuwidgets.LabelledEntry(
                         labelTxt=_('State ').rjust(26),
                         width=entryWidth, text=value)

        value = self.database.get(self.name, 'Country')
        if not value: value = 'Singapore'
        else: value = value[0]
        self.country = kusuwidgets.LabelledEntry(
                           labelTxt=_('Country ').rjust(26),
                           width=entryWidth, text=value)

        value = self.database.get(self.name, 'Contact')
        if not value: value = 'admin@cluster.hpc.org'
        else: value = value[0]
        self.contact = kusuwidgets.LabelledEntry(
                           labelTxt=_('Contact ').rjust(26),
                           width=entryWidth, text=value)
        self.contact.addCheck(kusuwidgets.verifyEmail)

        value = self.database.get(self.name, 'URL')
        if not value: value = 'http://cluster.hpc.org'
        else: value = value[0]
        self.url = kusuwidgets.LabelledEntry(
                       labelTxt=_('URL ').rjust(26),
                       width=entryWidth, text=value)
        self.url.addCheck(kusuwidgets.verifyURL)

        value = self.database.get(self.name, 'LatLong')
        if not value: value = 'N32.87 W117.22'
        else: value = value[0]
        self.latlong = kusuwidgets.LabelledEntry(
                           labelTxt=_('LatLong ').rjust(26),
                           width=entryWidth, text=value)


        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0, anchorLeft=1)
        self.screenGrid.setField(self.fqhn, col=0, row=1, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.clusterName, col=0, row=2, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.organisation, col=0, row=3, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.locality, col=0, row=4, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.state, col=0, row=5, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.country, col=0, row=6, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.contact, col=0, row=7, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.url, col=0, row=8, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.latlong, col=0, row=9, anchorLeft=1,
                                 padding=(0,0,0,-2))

    def validate(self):
        errList = []
        result, msg = self.fqhn.verify()
        if result is None:
            errList.append(_('FQHN field is empty'))
        elif not result:
            errList.append(msg)
        
        if not self.clusterName.value():
            errList.append(_('Cluster name field is empty'))

        result, msg = self.contact.verify()
        if result is None:
            errList.append(_('Contact field is empty'))
        elif not result:
            errList.append(msg)

        result, msg = self.url.verify()
        if result is None:
            errList.append(_('URL field is empty'))
        elif not result:
            errList.append(msg)

        if errList:
            errMsg = _('Please correct the following error(s):')
            for i, string in enumerate(errList):
                errMsg = errMsg + '\n\n' + str(i+1) + '. ' + string
            return False, errMsg
        else:
            return True, ''

    def formAction(self):
        """
        
        Nothing here yet.
        
        """
        self.database.put(self.name, 'FQHN', self.fqhn.value())
        self.database.put(self.name, 'ClusterName', self.clusterName.value())
        self.database.put(self.name, 'Organisation', self.organisation.value())
        self.database.put(self.name, 'Locality', self.locality.value())
        self.database.put(self.name, 'State', self.state.value())
        self.database.put(self.name, 'Country', self.country.value())
        self.database.put(self.name, 'Contact', self.contact.value())
        self.database.put(self.name, 'URL', self.url.value())
        self.database.put(self.name, 'LatLong', self.latlong.value())
