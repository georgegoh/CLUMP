#!/usr/bin/env python
#
# $Id$
#
# Node Group Editor Library
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
# Author: Alexey Tumanov (atumanov)

import sys
import os
import string
import re
from UserDict import UserDict
from sets import Set

NGE_TUI     = 0x01
NGE_CPY     = 0x02
NGE_DEL     = 0x04
NGE_PRNSTL  = 0x08
NGE_PRNALL  = 0x10
NGE_PRNONE  = 0x20

#emulate ternary cond. expression - only avail. in 2.5 & up :(
def ifelse(b, x, y): return ((b and [x]) or [y])[0]


class UnsupportedOSType(Exception):         pass
#NGE Exception hierarchy
class NodeGroupError(Exception):            pass
class NGEObjectException(NodeGroupError):   pass
class NGEDBException(NodeGroupError):       pass
class NGEInvalidRecord(NGEObjectException): pass
class NGEDBReadFail(NGEDBException):        pass
class NGEDBWriteFail(NGEDBException):       pass

class KusuDBRec(UserDict):
    ''' KusuDBRec is the abstract class defining the attributes & behavior
        of a Kusu DB table record object as well as its interface with the DB.
        Assumption: KusuDBRec.fields[0] is always the PK
    '''
    fields = ()
    table = None
    PKfld = property(lambda self: self.fields[0])
    PKval = property(lambda self: self.data[self.PKfld])

    def __init__(self, record=None, **kwargs):
        '''Re-defining native constructor to narrow down the utility of the child '''
        #initialize nodegroup record
        self.data = {}
        for key in self.fields:
            self.data[key] = None

        if record and (type(record) == tuple or type(record) == list):
            self.set(self.fields, record)

        if len(kwargs): #keyword args provided
            kwdict = {}
            for key in kwargs.keys():
                lkey = key.lower()
                if lkey in self.fields:
                    kwdict[lkey] = kwargs[key]
            self.update(kwdict)

    def __setitem__(self, key, item):
        '''KusuDBRec:[] Allows setting exactly one field for the given record '''
        key = key.lower()
        if key in self.fields:
            self.data[key] = item

    def __delitem__(self, key):
        #protect the primary key
        key = key.lower()
        if key != self.fields[0]:
            del self.data[key]

    def set(self, keys, values):
        '''KusuDBRec:set allows setting multiple fields for the given record'''
        for i in range(0, min(len(keys), len(values))):
            key = keys[i].lower()
            if key in self.fields:
                self[key] = values[i]

    def values(self):
        ''' KusuDBRec:values returns an ordered list of values '''
        rv = []
        for key in self.fields:
            if key in self.data.keys():
                rv.append(self.data[key])
        return rv

    def keys(self):
        ''' KusuDBRec:keys returns an ordered list of keys '''
        rv = []
        for key in self.fields:
            if key in self.data.keys():
                rv.append(key)
        return rv

    def __sub__(self,other):

        if not isinstance(other,KusuDBRec) or self.fields != other.fields:
            raise TypeError, "unsupported operand types(s) for '-': '%s' and '%s'"\
                             %(type(self),type(other))
        result = {}
        for key in self.fields:
            if not other.has_key(key) or self.data[key] != other[key]:
                result[key] = self.data[key]

        return result

    def syncFromDB(self,db):
        ''' updates this instance with information from the database
        '''
        try:
            assert(self.PKval)
        except AssertionError, msg:
            raise NGEInvalidRecord,"Invalid KusuDBRec record, missing primary key?"

        query = 'SELECT %s' + ', %s' * (len(self.fields[1:]) - 1) + \
                ' FROM %s WHERE %s = %s' % (self.table, self.PKfld, self.PKval)
        query = query % self.fields[1:]

        try:
            db.execute(query)
            rv = db.fetchone()
        except Exception,msg:
            raise NGEDBReadFail, msg

        self.set(self.fields[1:], rv)

    def syncToDB(self,db):
        ''' updates DB with information in this instance
        '''
        mode = 'update'
        try:
            assert(self.PKval)
        except AssertionError, msg:
            mode = 'insert'

        dbdict = {} #construct dict of non-Null values
        for f in self.fields[1:] : # skip PK
            if self.data[f] != None:
                dbdict[f] = self.data[f]
        if not dbdict:
            return

        if mode == 'update':
            query = "UPDATE %s SET %s = '%s'" + ", %s = '%s'"*(len(dbdict)-1) +\
                    " WHERE %s = %s"
            tpl = (self.table,)
            for t in dbdict.items():
                tpl += t #tuple concat
            tpl += (self.PKfld, self.PKval)
            query = query % tpl

        elif mode == 'insert':
            itemlst = dbdict.items()
            keylst = [k for k,v in itemlst]
            vallst = ["'%s'" %str(v) for k,v in itemlst]
            query = 'INSERT into %s (%s) values (%s)' %(self.table, \
                        string.join(keylst,',') , string.join(vallst,','))

        try:
            db.execute(query)
        except Exception,msg:
            raise NGEDBWriteFail,msg

        if mode == 'insert':
            #get the PK for the record just inserted
            try:
                db.execute("SELECT last_insert_id()")
                rv = db.fetchone()
            except Exception,msg:
                raise NGEDBReadFail,msg
    
            assert(len(rv)==1)
            self.data[self.PKfld] = rv[0]


    def eraseFromDB(self,db):
        ''' erase this record from the database '''
        try:
            assert(self.PKval)
        except AssertionError,msg:
            raise NGEInvalidRecord,msg

        try:
            db.execute("DELETE from %s where %s = %s" %(self.table, self.PKfld, self.PKval))
        except Exception,msg:
            raise NGEDBWriteFail,msg


class PartitionRec(KusuDBRec):
    fields = ( 'idpartitions', 'ngid', 'device', 'partition', 'mntpnt',
               'fstype', 'size', 'options', 'preserve'
             )
    table = 'partitions'


class NodeGroupRec(KusuDBRec):
    #assume NodeGroupRec.fields[0] is always the PK
    fields = ( 'ngid', 'repoid', 'ngname', 'installtype', 'ngdesc',
               'nameformat', 'kernel', 'initrd', 'kparams', 'type'
             )
    table = 'nodegroups'


        
class NodeGroup(NodeGroupRec):
    ''' NodeGroup class extends beyond NG table record representation - it
        captures the links of nodegroup records to other tables as well.
        In doing so, it allows the instance to encapsulate all the information
        pertinent to the specified NG record
    '''
    links =  ( 'comps', 'modules', 'nets', 'packs', 'scripts', 'parts' )
    linksDBmap={ 'comps':   ('ng_has_comp', 'cid'),
                 'modules': ('modules', 'module'),
                 'nets':    ('ng_has_net', 'netid'),
                 'packs':   ('packages', 'packagename'),
                 'scripts': ('scripts', 'script'),
                 'parts':   ('partitions', 'idpartitions')
               }

    def __init__(self, record=None, **kwargs):
        NodeGroupRec.__init__(self, record, **kwargs)

        for key in self.links:
            self.data[key] = None

        if len(kwargs): #keyword args provided
            kwdict = {}
            for key in kwargs.keys():
                lkey = key.lower()
                if lkey in self.links:
                    kwdict[lkey] = kwargs[key]
            self.update(kwdict)

    def __setitem__(self, key, item):
        '''Allows setting exactly one Nodegroup field for the given record '''
        key = key.lower()
        if key in self.links:
            if type(item) == list or type(item) == tuple:
                self.data[key] = item
        else:
            NodeGroupRec.__setitem__(self,key,item)

    def __sub__(self, other):
        ''' Allows diffing two objects of type NodeGroup. The result is a dict
            of keys for values that differ. The keys will map
            to the value from the first operand. This implies a-b != b-a
        '''
        if not isinstance(other,NodeGroup):
            raise TypeError, "unsupported operand types(s) for '-': '%s' and '%s'"\
                             %(type(self),type(other))

        result = NodeGroupRec.__sub__(self,other)

        for key in self.links:
            #all links should be lists
            try:
                assert(self.data[key] == None or type(self.data[key]) == list)
            except AssertionError,msg:
                raise
            if not other.has_key(key):
                result[key] = self.data[key]
            elif self.data[key] == None and other[key] == None:
                continue
            elif self.data[key] == None or other[key] == None:
                result[key] = self.data[key]
            else:
                #both operands have non-Null value
                l1 = self.data[key][:]
                l2 = other[key][:]
                sortkey = None
                if key == 'parts':
                    sortkey = lambda x: x['idpartitions']
                l1.sort(key = sortkey)
                l2.sort(key = sortkey)
                    
                if l1 != l2: #this uses UserDict.__cmp__
                    result[key] = self.data[key]
        return result

    def __getLinkByFK(self,db,link):

        db.execute("SELECT %s FROM %s WHERE ngid = %s" %(self.linksDBmap[link][1], \
                    self.linksDBmap[link][0], self.PKval))
        rv = db.fetchall()
        if link == 'parts':
            #special case - create list of PartitionRec instances
            self.data[link] = []
            for id, in rv:
                obj = PartitionRec(idpartitions = id)
                obj.syncFromDB(db)
                self.data[link].append(obj)
        else:
            self.data[link] = [x for x, in rv]

    def __putLinkByFK(self,db,link):
        #delete all records matching pk and add new ones
        #assume self.data[link] is non-Null

        query = "DELETE from %s where ngid = %s" %(self.linksDBmap[link][0], self.PKval)
        db.execute(query)

        if len(self.data[link]) < 1:
            return

        if link == 'parts': 
            #special case - iterate over the list of PartitionRec instances
            for p in self.data[link]:   #for each partition
                p[p.PKfld] = None       #give the Partition record new identity
                p['ngid'] = self.PKval  #if copied from other N.G. - correct ngid field
                p.syncToDB(db)
                db.execute('select last_insert_id()')
                rv = db.fetchone()
                p[p.PKfld] = rv[0]

        else:
            query = "INSERT into %s (ngid, %s) values " % (self.linksDBmap[link][0], \
                        self.linksDBmap[link][1])
            query += "(%s, '%s') " + ", (%s, '%s')"*(len(self.data[link])-1)

            tpl = ()
            for v in self.data[link]:
                tpl += self.PKval,v
            query = query % tpl

            try:
                db.execute(query)
            except Exception,msg:
                raise NGEDBWriteFail,'Failed syncing link=%s to DB with msg = %s\nQuery=%s' %(link,str(msg),query)


    def syncFromDB(self,db):
        ''' updates this instance with information from the database
        '''
        NodeGroupRec.syncFromDB(self,db)

        for l in self.links:
            self.__getLinkByFK(db,l)


    def syncToDB(self,db):
        ''' updates DB with information in this instance
        '''
        NodeGroupRec.syncToDB(self,db)

        try:
            assert(self.PKval)
        except AssertionError,msg:
            raise NGEInvalidRecord,msg

        for l in self.links:
            if self.data[l] != None: #don't touch the Null links
                self.__putLinkByFK(db,l)

    def eraseFromDB(self,db):
        ''' erase this record from the database '''
        try:
            assert(self.PKval)
        except AssertionError,msg:
            raise NGEInvalidRecord,msg

        for l in self.links:
            if self.data[l] !=None:
                try:
                    db.execute("DELETE from %s where ngid = %s" % (self.linksDBmap[l][0], self.PKval) )
                except Exception,msg:
                    raise NGEDBWriteFail,msg

        NodeGroupRec.eraseFromDB(self,db)

def RpmNameSplit(packname):
    ''' return a tuple (name,version,release,arch,ext)
    '''
    rv = ['','','','','']
    try:
        nvr,rv[3],rv[4] = packname.rsplit('.',2)
    except Exception,msg:
        raise Exception, str(msg)+"\npackname = %s,rv = %s" %(packname,str(rv))
    rv[0:2] = nvr.rsplit('-',2)
    return tuple(rv)

import snack
from kusu.ui.text.USXscreenfactory import USXBaseScreen
from kusu.ui.text.USXnavigator import *

class NGEPluginBase(USXBaseScreen):
    name= 'Generic Plugin Name'
    msg = ''
    buttons = ['next_button', 'prev_button']
    hotkeysDict = {}

    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.ngid = None
        self.interactive = False #default to non-interactive

    def isInteractive(self):
        return self.interactive

    def setCallbacks(self):

        self.buttonsDict['next_button'].setCallback_(self.NextAction)
        self.buttonsDict['prev_button'].setCallback_(self.PrevAction)

    def NextAction(self, data=None):
        return NAV_FORWARD

    def PrevAction(self, data=None):
        return NAV_BACK

    def drawImpl(self):
        """
        All screen drawing code goes here. Don't draw the buttons as well, this
        is already done for you.
        """
        self.screenGrid = snack.Grid(1, 1)
        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                 width=self.gridWidth),
                                 col=0, row=0)

    def validate(self):
        """Validation code goes here. Activated when 'Next' button is pressed."""
        return True, 'Success'

    def formAction(self):
        """Any action other than validation that takes place after the
           'Next button is pressed.
        """
        self.add()

    def add(self):
        ''' add method gets called for every component associated with the N.G.
            regardless of whether the plugin is interactive or not.
            It's called directly for non-interactive plugins, and via formAction()
            method for the interactive ones.
        '''
        pass

    def remove(self):
        ''' remove method gets called for every component disassociated from the N.G.
        '''
        pass
