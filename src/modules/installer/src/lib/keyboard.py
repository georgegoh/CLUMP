#!/usr/bin/env python
# $Id: keyboard.py 237 2007-04-05 08:57:10Z ggoh $
#
# Kusu Text Installer Keyboard Selection Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__versio__ = "$Revision: 237 $"

import __init__
import logging
import snack
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT

class KeyboardSelectionScreen(screenfactory.BaseScreen):
    """This screen asks for keyboard."""
    name = _('Keyboard')
    context = 'Keyboard'
    msg = _('Please choose your keyboard:')
    buttons = []

    def setCallbacks(self):
        """
        
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        
        """

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 2)
        
        instruction = snack.Label(self.msg)
        self.screenGrid.setField(instruction, col=0, row=0)
        self.listbox = snack.Listbox(8, scroll=1, returnExit=1)
        keyboardList = modelDict.keys()
        keyboardList.sort()
        for name in keyboardList:
            self.listbox.append(name, name)

        value = self.database.get(self.context, 'Keyboard')
        if not value: value = 'us'
        else: value = value[0]
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
        """
        
        Store the keyboard settings.
        
        """
        keyboard = self.listbox.current()
        self.database.put(self.context, 'Keyboard', keyboard)

    def executeCallback(self, obj):
        if obj is self.listbox:
            return True
        return False

# The following is data taken from the rhpl package 'keyboard_models.py',
# which is licensed under GPL v2.
# NOTE: to add a keyboard model to this dict, copy the comment
# above all of them, and then the key should be the console layout
# name.  val is [_('keyboard|Keyboard Name'), xlayout, kbmodel,
# variant, options]
modelDict = {
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ar-azerty'               : [_('keyboard|Arabic (azerty)'), 'us,ara', 'pc105', 'azerty', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ar-azerty-digits'        : [_('keyboard|Arabic (azerty/digits)'), 'us,ara', 'pc105', 'azerty_digits', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ar-digits'               : [_('keyboard|Arabic (digits)'), 'us,ara', 'pc105', 'digits', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ar-qwerty'               : [_('keyboard|Arabic (qwerty)'), 'us,ara', 'pc105', 'qwerty', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ar-qwerty-digits'        : [_('keyboard|Arabic (qwerty/digits)'), 'us,ara', 'pc105', 'qwerty_digits', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'be-latin1'               : [_('keyboard|Belgian (be-latin1)'), 'be', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ben'                      : [_('keyboard|Bengali (Inscript)'), 'us,in', 'pc105', 'ben', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ben-probhat'             : [_('keyboard|Bengali (Probhat)'), 'us,in', 'pc105', 'be_probhat', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'bg'                      : [_('keyboard|Bulgarian'), 'us,bg', 'pc105', '', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'br-abnt2'                : [_('keyboard|Brazilian (ABNT2)'), 'br', 'abnt2', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'cf'                      : [_('keyboard|French Canadian'), 'ca(fr)', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'croat'                   : [_('keyboard|Croatian'), 'hr', 'pc105', '', '' ],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'cz-us-qwertz'            : [_('keyboard|Czechoslovakian (qwertz)'), 'us,cz', 'pc105', '', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'cz-lat2'                 : [_('keyboard|Czechoslovakian'), 'cz', 'pc105', 'qwerty', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'de'                      : [_('keyboard|German'), 'de', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'de-latin1'               : [_('keyboard|German (latin1)'), 'de', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'de-latin1-nodeadkeys'    : [_('keyboard|German (latin1 w/ no deadkeys)'), 'de', 'pc105', 'nodeadkeys', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'dev'                     : [_('keyboard|Devanagari (Inscript)'), 'us,dev', 'pc105', '', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'dvorak'                   : [_('keyboard|Dvorak'), 'us', 'pc105', 'dvorak', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'dk'                      : [_('keyboard|Danish'), 'dk', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'dk-latin1'               : [_('keyboard|Danish (latin1)'), 'dk', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'es'                      : [_('keyboard|Spanish'), 'es', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'et'                      : [_('keyboard|Estonian'), 'ee', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'fi'                      : [_('keyboard|Finnish'), 'fi', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'fi-latin1'               : [_('keyboard|Finnish (latin1)'), 'fi', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'fr'                      : [_('keyboard|French'), 'fr', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'fr-latin9'               : [_('keyboard|French (latin9)'), 'fr', 'pc105', 'latin9', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'fr-latin1'               : [_('keyboard|French (latin1)'), 'fr', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'fr-pc'                   : [_('keyboard|French (pc)'), 'fr', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'fr_CH'                   : [_('keyboard|Swiss French'), 'fr_CH', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'fr_CH-latin1'            : [_('keyboard|Swiss French (latin1)'), 'ch', 'pc105', 'fr', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'gr'                      : [_('keyboard|Greek'), 'us,gr', 'pc105', '', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'guj'                     : [_('keyboard|Gujarati (Inscript)'), 'us,in', 'pc105', 'guj', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'gur'                     : [_('keyboard|Punjabi (Inscript)'), 'us,gur', 'pc105', '', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'hu'                      : [_('keyboard|Hungarian'), 'hu', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'hu101'                   : [_('keyboard|Hungarian (101 key)'), 'hu', 'pc105', 'qwerty', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'is-latin1'               : [_('keyboard|Icelandic'), 'is', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'it'                      : [_('keyboard|Italian'), 'it', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'it-ibm'                  : [_('keyboard|Italian (IBM)'), 'it', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'it2'                     : [_('keyboard|Italian (it2)'), 'it', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'jp106'                   : [_('keyboard|Japanese'), 'jp', 'jp106', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'us'               : [_('keyboard|Korean'), 'us', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'la-latin1'               : [_('keyboard|Latin American'), 'latam', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'mk-utf'                  : [_('keyboard|Macedonian'), 'us,mkd', 'pc105', '','grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'nl'                      : [_('keyboard|Dutch'), 'nl', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'no'                      : [_('keyboard|Norwegian'), 'no', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'pl2'                      : [_('keyboard|Polish'), 'pl', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'pt-latin1'               : [_('keyboard|Portuguese'), 'pt', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ro_win'                  : [_('keyboard|Romanian'), 'ro', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ru'                      : [_('keyboard|Russian'), 'us,ru', 'pc105', '', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ru-cp1251'               : [_('keyboard|Russian (cp1251)'), 'us,ru', 'pc105', '', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ru.map.utf8ru'           : [_('keyboard|Russian (utf8ru)'), 'us,ru', 'pc105', '', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ru-ms'                   : [_('keyboard|Russian (Microsoft)'), 'us,ru', 'pc105', '', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ru1'                     : [_('keyboard|Russian (ru1)'), 'us,ru', 'pc105', '', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ru2'                     : [_('keyboard|Russian (ru2)'), 'us,ru', 'pc105', '', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ru_win'                  : [_('keyboard|Russian (win)'), 'us,ru', 'pc105', 'winkeys', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'sr-cy'                 : [_('keyboard|Serbian'), 'srp', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'sv-latin1'               : [_('keyboard|Swedish'), 'se', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'sg'                      : [_('keyboard|Swiss German'), 'ch', 'pc105', 'de_nodeadkeys', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'sg-latin1'               : [_('keyboard|Swiss German (latin1)'), 'ch', 'pc105', 'de_nodeadkeys', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'sk-qwerty'               : [_('keyboard|Slovakian'), 'sk', 'pc105', '', 'qwerty'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'slovene'                 : [_('keyboard|Slovenian'), 'si', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'tml-inscript'            : [_('keyboard|Tamil (Inscript)'), 'us,in', 'pc105', 'tam', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'tml-uni'                 : [_('keyboard|Tamil (Typewriter)'), 'us,in', 'pc105', 'tam_TAB', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'trq'                     : [_('keyboard|Turkish'), 'tr', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'uk'                      : [_('keyboard|United Kingdom'), 'gb', 'pc105', '', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'ua-utf'                  : [_('keyboard|Ukrainian'), 'us,ua', 'pc105', '', 'grp:shifts_toggle,grp_led:scroll'],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'us-acentos'              : [_('keyboard|U.S. International'), 'us', 'pc105', 'intl', ''],
    # Translators: the word before the bar is just context and
    # doesn't need to be translated. Only after will be translated.
    'us'                      : [_('keyboard|U.S. English'), 'us', 'pc105', '', ''],
}
