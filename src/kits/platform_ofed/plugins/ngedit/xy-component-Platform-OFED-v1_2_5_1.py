# Copyright (C) 2007 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
# $Id$
#
import os
import glob
import snack
import string
from kusu.ngedit.ngedit import NGEPluginBase
from kusu.ui.text import USXkusuwidgets as kusuwidgets

MAXIBIFCNT=8

class NGPlugin(NGEPluginBase):
    name= 'OFED Kit'
    msg = 'OFED Kit Message'

    def __init__(self, database, kusuApp=None, gridWidth=45):
        NGEPluginBase.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.setHelpLine("Please enter the number of IPoIB interfaces desired.")
        self.interactive = True

    def drawImpl(self):
        """
        All screen drawing code goes here. Don't draw the buttons as well, this
        is already done for you.
        """
        self.screenGrid = snack.Grid(1, 2)
        msg = "Please enter the number of IPoIB interfaces you wish to configure."
        self.__ifacecnt = kusuwidgets.LabelledEntry(labelTxt="Number of interfaces: ",
                text = "", width=5, password=0, returnExit = 0)
        self.screenGrid.setField(snack.TextboxReflowed(text=msg, width=self.gridWidth),
                                 0,0, (0,0,0,0))
        self.screenGrid.setField(self.__ifacecnt, 0,1, (0,0,0,0))

    def validate(self):

        cnt = self.__ifacecnt.value().strip()
        if not cnt.isdigit():
            return False, "The value should be a positive integer between 0 & " +\
                          "%s inclusive." %MAXIBIFCNT
        cnt = int(cnt)
        if cnt<0 or cnt>MAXIBIFCNT:
            return False, "The value should be a positive integer between 0 & " +\
                          "%s inclusive." %MAXIBIFCNT

        return True, "Success"
        

    def add(self):
        cnt = int(self.__ifacecnt.value().strip())
        if cnt>0:
            self.selector.popupMsg("IPoIB configuration reminder", "Please create IPoIB "+\
                "networks using netedit. Subsequently, rerun ngedit to associate this " +\
                "nodegroup with newly created IB interfaces.")
        
    def remove(self):
        assert(self.ngid)
        query = '''DELETE FROM ng_has_net WHERE ngid = %s and netid in ( select netid 
                   from networks where device like 'ib%%')''' %self.ngid
        try:
            self.database.execute(query)
        except:
            #if delete fails - just forge on
            pass
