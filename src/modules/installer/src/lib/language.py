#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Language Selection Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision: 237 $"

import __init__
import os
#import logging
import snack
import gettext
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT

class LanguageSelectionScreen(screenfactory.BaseScreen):
    """This screen asks for language."""
    name = _('Language')
    context = 'Language'
    msg = _('Please choose your language for installation:')
    buttons = []

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 2)
        
        instruction = snack.Label(self.msg)
        self.screenGrid.setField(instruction, col=0, row=0)
        self.listbox = snack.Listbox(8, scroll=1, returnExit=1)

        kusuroot = os.environ.get('KUSU_ROOT', None)
        if kusuroot and os.path.exists('%s/etc/lang-table' % kusuroot):     
            langTable = open('%s/etc/lang-table' % kusuroot)

        rows = langTable.readlines()
        self.langMap = {}
        for row in rows:
            attr = row.split('\t')
            if len(attr) < 6:
                raise Exception, "Row in lang-table has < 6 elements\n"+ \
                                 row
            self.langMap[attr[0]] = (attr[1], attr[2], attr[3], attr[4], attr[5])
        languages = self.langMap.keys()
        languages.sort()
        for language in languages:
            self.listbox.append(language, self.langMap[language])

        value = self.database.get(self.context, 'Language')
        if not value: value = self.langMap['English']
        else:
            for k,v in self.langMap.iteritems():
                if v[0] == value[0]:
                    value = v
        self.listbox.setCurrent(value)

        self.screenGrid.setField(self.listbox, col=0, row=1,
                                 padding=(0,1,0,-1))

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
        if langAttr[0] != 'en':
            try:
                t = gettext.translation('kusu', 'locale', languages=[langAttr[0]])
                t.install()
            except IOError, e:
                snack.ButtonChoiceWindow(self.screen, 'Cannot display language.',
                                     'Selected language cannot be shown' + \
                                     ' on this display. This installation ' + \
                                     'will proceed in English.', buttons=['Ok'])
        self.database.put(self.context, 'Language', langAttr[0])

    def executeCallback(self, obj):
        if obj is self.listbox:
            return True
        return False
