#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Cluster Info Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.

import snack
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
from kusu.util.util import verifyURL, verifyEmail, verifyFQDN
NAV_NOTHING = -1

class ClusterInfoScreen(screenfactory.BaseScreen):
    """Collects info about the cluster."""
    name = 'Cluster Info'
    context = 'Cluster Info'
    profile = context
    msg = _('Please enter the following information:')
    buttons = [_('Clear All')]

    def setCallbacks(self):
        """
        
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        
        """
        self.buttonsDict[_('Clear All')].setCallback_(self.clearAllFields)

    def clearAllFields(self):
        self.database.put(self.context, 'FQHN', '')
        self.database.put(self.context, 'ClusterName', '')
        self.database.put(self.context, 'Organisation', '')
        self.database.put(self.context, 'Locality', '')
        self.database.put(self.context, 'State', '')
        self.database.put(self.context, 'Country', '')
        self.database.put(self.context, 'Contact', '')
        self.database.put(self.context, 'URL', '')
        self.database.put(self.context, 'LatLong', '')

        try:
            self.kiprofile[self.profile]
        except KeyError:
            self.kiprofile[self.profile] = {}
        self.kiprofile[self.profile]['FQHN'] = ''
        self.kiprofile[self.profile]['ClusterName'] = ''
        self.kiprofile[self.profile]['Organisation'] = ''
        self.kiprofile[self.profile]['Locality'] = ''
        self.kiprofile[self.profile]['State'] = ''
        self.kiprofile[self.profile]['Country'] = ''
        self.kiprofile[self.profile]['Contact'] = ''
        self.kiprofile[self.profile]['URL'] = ''
        self.kiprofile[self.profile]['LatLong'] = ''

        return NAV_NOTHING

    def drawImpl(self):
        """Draw onscreen all entry fields associated with Cluster Information."""
        self.screenGrid = snack.Grid(1, 9)
        entryWidth = 30

        self.clusterName = kusuwidgets.LabelledEntry(
                               labelTxt=_('Cluster Name ').rjust(26),
                               width=entryWidth)

        self.organisation = kusuwidgets.LabelledEntry(
                                labelTxt=_('Organisation ').rjust(26),
                                width=entryWidth)

        self.locality = kusuwidgets.LabelledEntry(
                            labelTxt=_('Locality ').rjust(26),
                            width=entryWidth)

        self.state = kusuwidgets.LabelledEntry(
                         labelTxt=_('State ').rjust(26),
                         width=entryWidth)

        self.country = kusuwidgets.LabelledEntry(
                           labelTxt=_('Country ').rjust(26),
                           width=entryWidth)

        self.contact = kusuwidgets.LabelledEntry(
                           labelTxt=_('Contact ').rjust(26),
                           width=entryWidth)
        self.contact.addCheck(verifyEmail)

        self.url = kusuwidgets.LabelledEntry(
                       labelTxt=_('URL ').rjust(26),
                       width=entryWidth)
        self.url.addCheck(verifyURL)

        self.latlong = kusuwidgets.LabelledEntry(
                           labelTxt=_('LatLong ').rjust(26),
                           width=entryWidth)

        self.populateFields()

        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0, anchorLeft=1)
        self.screenGrid.setField(self.clusterName, col=0, row=1, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.organisation, col=0, row=2, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.locality, col=0, row=3, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.state, col=0, row=4, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.country, col=0, row=5, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.contact, col=0, row=6, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.url, col=0, row=7, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.latlong, col=0, row=8, anchorLeft=1,
                                 padding=(0,0,0,-2))

    def populateFields(self):
        """Populate all fields with data retrieved from the data source."""
        profile = self.kiprofile[self.profile]

        try:
            self.clusterName.setEntry(profile['ClusterName'])
            self.organisation.setEntry(profile['Organisation'])
            self.locality.setEntry(profile['Locality'])
            self.state.setEntry(profile['State'])
            self.country.setEntry(profile['Country'])
            self.contact.setEntry(profile['Contact'])
            self.url.setEntry(profile['URL'])
            self.latlong.setEntry(profile['LatLong'])
        except KeyError:
            self.clusterName.setEntry('Our Cluster')
            self.organisation.setEntry('OSGDC')
            self.locality.setEntry('Singapore')
            self.state.setEntry('Singapore')
            self.country.setEntry('Singapore')
            self.contact.setEntry('admin@cluster.osgdc.org')
            self.url.setEntry('http://cluster.hpc.org')
            self.latlong.setEntry('N1.223323 E103.859761')
   
    def validate(self):
        """Runs validation checks for all user input."""
        errList = []
        
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
        
        Store the values entered here into the database.
        
        """
        try:
            profile = self.kiprofile[self.profile]
        except KeyError:
            profile = {}
            self.kiprofile[self.profile] = profile

        profile['ClusterName'] = self.clusterName.value()
        profile['Organisation'] = self.organisation.value()
        profile['Locality'] = self.locality.value()
        profile['State'] = self.state.value()
        profile['Country'] = self.country.value()
        profile['Contact'] = self.contact.value()
        profile['URL'] = self.url.value()
        profile['LatLong'] = self.latlong.value()


    def restoreProfileFromSQLCollection(db, context, kiprofile):
        """
        Reads data from SQLiteCollection db according to context and fills
        profile.

        Arguments:
        db -- an SQLiteCollection object ready to accept data
        context -- the context to use to access data in db
        kiprofile -- the profile (a dictionary) with data to commit
        """

        clusterinfoContext = db.get(context)
        clusterinfo_dict = {}
        for property in clusterinfoContext:
            clusterinfo_dict[property[2]] = property[3]

        kiprofile[context] = clusterinfo_dict

        return True

    def saveProfileToSQLCollection(db, context, kiprofile):
        """
        Writes data from profile to SQLiteCollection db according to context.

        Arguments:
        db -- an SQLiteCollection object ready to accept data
        context -- the context to use to access data in db
        kiprofile -- the profile (a dictionary) with data to commit
        """

        clusterinfo = kiprofile[context]

        for setting in clusterinfo.keys():
            db.put(context, setting, clusterinfo[setting])

        return True

    dbFunctions = {'MySQL': None,
                   'SQLite': None,
                   'SQLColl': (restoreProfileFromSQLCollection,
                               saveProfileToSQLCollection)}

