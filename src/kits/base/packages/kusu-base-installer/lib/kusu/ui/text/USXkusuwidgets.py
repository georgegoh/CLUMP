#!/usr/bin/env python
#
# $Id: USXkusuwidgets.py 1196 2007-06-06 22:33:14Z atumanov $
#
# Kusu Text Installer Widgets.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
"""This module contains a number of widgets used in the Text Installer Framework."""

from kusu.ui.text.kusuwidgets import *
import string

class USXButton(Button):

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

class ProgressOutputWindow(ProgressDialogWindow):

    def __init__(self, snackScreen, title, msg, width=30, height=1,scroll=0):
        self.__width = width
        self.__height = height
        self.snackScreen = snackScreen
        self.msgbox = snack.GridForm(snackScreen, title, 1,1)
        self.textbox = snack.Textbox(width=width,height=height,text=msg,scroll=scroll,wrap=0)
        self.msgbox.add(self.textbox, 0,0)
        self.msgbox.draw()
        snackScreen.refresh()

    def setText(self, text):
        (newtext,width,height) = snack.reflow(text,self.__width,0,0) #zero flexibility
        msg = string.join(newtext.split('\n')[-self.__height:], '\n')
        ProgressDialogWindow.setText(self,msg)

    def draw(self):
        self.msgbox.draw()

    def refresh(self):
        self.snackScreen.refresh()
