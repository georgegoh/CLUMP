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

import snack

LEFT = -1
CENTER = 0
RIGHT = 1

from navigator import NAV_QUIT, NAV_FORWARD, NAV_BACK, NAV_NOTHING, NAV_FORWARD_NO_VALIDATION

class Button(snack.Button):
    labelTxt = ''

    def __init__(self, text):
        snack.Button.__init__(self, text)
        labelTxt = text
        self.callback_ = None

    def setCallback_(self, method, args=None):
        self.callback_ = method
        self.args = args

    def activateCallback_(self):
        if self.callback_:
            if self.args is None:
                result = self.callback_()
            elif type(self.args) == type(()) or type(self.args) == type([]):
                result = self.callback_(*self.args)
            else:
                result = self.callback_(self.args)
            if result in [NAV_QUIT, NAV_FORWARD, NAV_BACK,\
                          NAV_NOTHING, NAV_FORWARD_NO_VALIDATION]:
                return result


class LabelledEntry(snack.Widget, snack.Grid):
    label = None
    entry = None
    labelTxt = ''

    def value(self):
        return self.entry.value()

    def setLabel(self, text):
        self.labelTxt = text
        self.label.setText(text)

    def setEntry(self, text):
        return self.entry.set(text)

    def setEnabled(self, enable):
        if enable:
            sense = snack.FLAGS_RESET
        else:
            sense = snack.FLAGS_SET
        self.entry.setFlags(snack.FLAG_DISABLED, sense)

    def addCheck(self, checkFn):
        """Add a check function to the verification of this object.

           addCheck(self, checkFn)

           checkFn must be a function that takes in one text arg, and returns
           True or False, depending on the result of the check.
           
        """
        self.checksList.append(checkFn)

    def verify(self):
        """Verifies the text entered by running all checks registered with the
           addCheck function.

           Returns (False, message) tuple on the first check that fails.
           Returns (True, None) if all checks pass.

        """
        if not self.value():
            return None, None
        for check in self.checksList:
            result, msg = check(self.value())
            if result is not True:
                return result, msg
        return True, None

    def __init__(self, labelTxt, width, text="", hidden=0, password=0, scroll=1,
                 returnExit=0):
        snack.Grid.__init__(self, 2, 1)
        self.checksList = []
        self.labelTxt = labelTxt
        self.label = snack.Label(labelTxt)
        self.entry = snack.Entry(width, text, hidden, password, scroll, returnExit)

        # Add hook to use snack setCallback() for hot text events.
        self.w = self.entry
        self.setField(self.label, col=0, row=0, anchorLeft=1)
        self.setField(self.entry, col=1, row=0, anchorRight=1)


class ColumnListbox(snack.Grid):
    """A ColumnListbox behaves like a normal Listbox widget, but lets the
       programmer define multiple columns of data for the listbox.
    """
    height = 0
    colLabels = []
    colWidths = []
    justification = []
    length = property((lambda self : len(self.listbox.key2item)), None,
                      doc='The number of items in this listbox.')

    def __init__(self, height, colWidths, colLabels, justification, returnExit=1):
        if len(colLabels) is not len(justification):
            raise Exception, _("The lengths of colLabels and \
                              justification must be the same.")
        
        self.height = height
        self.colLabels = colLabels
        self.colWidths = colWidths
        self.justification = justification

        row = 0
        if colLabels:   # draw header row if labels are defined.
            snack.Grid.__init__(self, 1, 2)
            hdr = self.__createHeader()
            self.setField(hdr, col=0, row=row)
            row = row + 1
        else:
            snack.Grid.__init__(self, 1, 1)

        self.listbox = snack.Listbox(height, scroll=1, returnExit=returnExit,
                                     showCursor=0)
        self.setField(self.listbox, col=0, row=row)
        

    def __createHeader(self):
        """Draw the header labels."""
        totalWidth = 0
        for width in self.colWidths:
            totalWidth = totalWidth + width
        
        justification = []
        for i in range(len(self.colLabels)):
            justification.append(CENTER)
        hdrText = self.createRowText(self.colLabels, justification)
        hdr = snack.Label(hdrText)
        return hdr

    def addRow(self, colTexts, objRef=None):
        rowText = self.createRowText(colTexts, justification=self.justification)
        self.listbox.append(rowText, objRef)

    def createRowText(self, colTexts, justification):
        if len(self.colWidths) is not len(colTexts):
            raise Exception, "Number of items in colWidths does not match \
                              number of items in colTexts."
        rowText = ''
        for i, text in enumerate(colTexts):
            if not text:
                text = ''
            currentColWidth = self.colWidths[i]
            currentColText = text[:currentColWidth]

            if justification[i] is LEFT:
                justifiedColText = ' ' + currentColText.ljust(currentColWidth-1)
            if justification[i] is CENTER:
                justifiedColText = currentColText.center(currentColWidth)
            if justification[i] is RIGHT:
                justifiedColText = currentColText.rjust(currentColWidth-1) + ' '

            rowText = rowText + justifiedColText
        return rowText

    def current(self):
        if not self.length:
            return None
        else:
            return self.listbox.current()

    def setCurrent(self, item):
        self.listbox.setCurrent(item)

    def setCallback_(self, obj, data = None):
        self.listbox.setCallback(obj, data)

    def clear(self):
        self.listbox.clear()


class ProgressDialogWindow(object):

    msgbox = None
    textbox = None
    snackScreen = None

    def __init__(self, snackScreen, title, msg):
        self.snackScreen = snackScreen
        self.msgbox = snack.GridForm(snackScreen, title, 1,1)
        self.textbox = snack.TextboxReflowed(30, msg)
        self.msgbox.add(self.textbox,0, 0)
        self.msgbox.draw()
        snackScreen.refresh()

    def setText(self, text):
        self.textbox.setText(text)

    def close(self):
        self.snackScreen.popWindow()
