#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Widgets.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
"""This module contains a number of widgets used in the Text Installer Framework."""

import kusu.ui.text.kusuwidgets

class USXButton(kusu.ui.text.kusuwidgets.Button):

    def activateCallback_(self):
        if self.callback_:
            if self.args is None:
                result = self.callback_()
            elif type(self.args) == type(()) or type(self.args) == type([]):
                result = self.callback_(*self.args)
            else:
                result = self.callback_(self.args)
            return result #pass the result as is
        return False #callback not handled

