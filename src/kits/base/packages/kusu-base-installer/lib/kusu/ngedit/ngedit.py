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


class UnsupportedOSType(Exception):             pass
#NGE Exception hierarchy
class NodeGroupError(Exception):                pass
class NGEObjectException(NodeGroupError):       pass
class NGEDBException(NodeGroupError):           pass
class NGEInvalidRecord(NGEObjectException):     pass
class NGEPartSchemaError(NGEObjectException):   pass
class NGEDBReadFail(NGEDBException):            pass
class NGEDBWriteFail(NGEDBException):           pass

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

    def prettyPrint(self):
        ''' virtual print '''
        pass


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

    def prettyPrint(self):
        print "Name:            ", self.data['ngname']
        print "Desc:            ", self.data['ngdesc']
        print "Type:            ", self.data['type']
        print "Install Type:    ", self.data['installtype']
        print "Nodename Format: ", self.data['nameformat']
        print "Kernel:          ", self.data['kernel']
        print "Kernel Params:   ", self.data['kparams']
        print "Initrd:          ", self.data['initrd']


        
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

def seq2tplstr(seq):
    '''convert a sequence to a tuple string representation without a trailing comma
    '''
    if not seq:
        return None
    try:
        if len(seq) == 1:
            tplstr = '(%s)' % str(seq[0])
        else:
            tplstr = str(tuple(seq))
        return tplstr
    except:
        return None

from kusu.ngedit.partition import *
from kusu.partitiontool import partitiontool

LEFT    = -1
CENTER  = 0
RIGHT   = 1
class PartSchema:
    def __init__(self, diskprofile = None ):
        #schema and PartRecList should be tightly related and reflect each other;
        #to prevent them being out of sync, they should be managed in one place;
        #therefore, disallow passing them to PartSchema's ctor
    
        if diskprofile:
            self.disk_profile = diskprofile
        else:
            self.disk_profile = partitiontool.DiskProfile(fresh=True, probe_fstab=False)

        self.schema = None
        self.PartRecList = None
        self.pk2dict = {}   #maps PartitionRec.PKval to the associated schema dict

    def mycreateSchema(self, part_rules=None):
        ''' creates a partition schema compatible with nodeinstaller's with addition
            of 'inst' to LVs, VGs, Partitions, and PVs. Largely builds on 
            nodeinstaller's partition API
        '''
        diskprofile = self.disk_profile
        if part_rules == None:
            part_rules = self.PartRecList
        else:
            self.PartRecList = part_rules
    
        schema = {'disk_dict':{},'vg_dict':{}}
        vg_list = getVGList(part_rules, diskprofile)
        part_list = getPartList(part_rules, diskprofile)
        lv_list = getLVList(part_rules, diskprofile)
    
        # create the volume groups first.
        try:
            for vginfo in vg_list:
                vgname = vginfo['device']
                vg_extent_size = translatePartitionOptions(vginfo['options'], 'vg')[1]
                schema['vg_dict'][vgname] = {'pv_list':[], 'lv_dict':{},
                                             'extent_size':vg_extent_size,
                                             'name':vgname, 'instid': vginfo.PKval}
                self.pk2dict[vginfo.PKval] = schema['vg_dict'][vgname]
    
            # create the normal volumes.
            for partinfo in part_list:
                fs = translateFSTypes(partinfo['fstype'])
                self.createPartition(partinfo, schema['disk_dict'], schema['vg_dict'])
                pv, vg_name = translatePartitionOptions(partinfo['options'], 'pv')
                if pv:
                    handlePV(partinfo, vg_name, schema['vg_dict'])
            # renumber spanning partitions - resolve 'N'
            for disk in schema['disk_dict'].itervalues():
                part_dict = disk['partition_dict']
                if part_dict.has_key('N'):
                    partition = part_dict['N']
                    part_dict[len(part_dict)] = partition
                    del part_dict['N']
    
            # create the logical volumes.
            for lvinfo in lv_list:
                lv, vg_name = translatePartitionOptions(lvinfo['options'],'lv')
                if lv: 
                    handleLV(lvinfo, vg_name, schema['vg_dict'])
                    #associate with corresponding PartitionRec instance
                    vg = schema['vg_dict'][vg_name.strip()]
                    lv_name = lvinfo['device']
                    vg['lv_dict'][lv_name]['instid'] = lvinfo.PKval
                    vg['lv_dict'][lv_name]['preserve'] = lvinfo['preserve']
                    self.pk2dict[lvinfo.PKval] = vg['lv_dict'][lv_name]
    
            attachPVsToVGs(diskprofile, schema['vg_dict'])
    
            preserve_types = Partition.native_type_dict.values()
            preserve_fs = DiskProfile.fsType_dict.keys()
            preserve_mntpnt = diskprofile.mountpoint_dict.keys()
            preserve_lv = [lv.name for lv in diskprofile.lv_dict.values()]
            schema['preserve_types'] = preserve_types
            schema['preserve_fs'] = preserve_fs
            schema['preserve_mntpnt'] = preserve_mntpnt
            schema['preserve_lv'] = preserve_lv
    
        except ValueError:
            raise InvalidPartitionSchema, "Couldn't parse one of the lines."
    
        self.schema = schema
        return self.schema
    
    def createPartition(self, partinfo, disk_dict, vg_dict):
        """ Create a new partition and add it to the supplied disk dictionary."""
        try:
            disknum = int(partinfo['device'])
            part_no = translatePartitionNumber(partinfo['partition'])
        except ValueError:
            if partinfo['device'].lower() == 'n':
                handleSpanningPartition(partinfo, disk_dict, vg_dict)
                disknum = 1
                part_no = 'N'
            else:
                raise InvalidPartitionSchema, "Couldn't translate the disknum/partition number."
        try:
            size = translatePartitionSize(partinfo['size'])
            fs = translateFSTypes(partinfo['fstype'])
            mountpoint = translateMntPnt(partinfo['mntpnt'])
            fill = translatePartitionOptions(partinfo['options'], 'fill')[0]
        except ValueError:
            raise InvalidPartitionSchema, "Couldn't parse one of the Partition fields. " + \
                                          "disknum=%s, size=%s, fs=%s, mntpnt=%s, fill=%s, " + \
                                          "part_no=%s" % (partinfo['device'], partinfo['size'], \
                                          partinfo['fstype'], partinfo['mntpnt'], \
                                          partinfo['options'], partinfo['partition'])
     
        if part_no != 'N' and part_no <= 0:
            raise InvalidPartitionSchema, "Partition number cannot be less than 1."
        partition = {'size_MB': size, 'fill': fill, 
                     'fs': fs, 'mountpoint': mountpoint,
                     'instid':partinfo.PKval, 'preserve': partinfo['preserve'] } #the only change
    
        if disk_dict.has_key(disknum): disk = disk_dict[disknum]
        else: disk = {'partition_dict': {}}
        disk['partition_dict'][part_no] = partition
        self.pk2dict[partinfo.PKval] = partition    #add the pk->dict mapping for the partition
        disk_dict[disknum] = disk

    def getDictByPK(self,pk):
        try:
            return self.pk2dict[pk]
        except KeyError:
            return None

    def getPartRecByPK(self,pk):
        for p in self.PartRecList:
            if p.PKval == pk:
                return p
        return None

    def addPartRec(self,record):
        ''' adds a new PartitionRec object to the PartRecList - assumes it's not there yet '''
        if not self.PartRecList:
            self.PartRecList = []
        self.PartRecList.append(record)

    def updatePartRec(self,record):
        ''' updates existing PartitionRec object with the new one
            raise error if the matching record not found
        '''

        for i in xrange(len(self.PartRecList)):
            p = self.PartRecList[i]
            if p.PKval == record.PKval:
                del self.PartRecList[i]
                self.PartRecList.insert(i,record)

    def isPartition(self,id):
        for p in self.PartRecList:
            if p.PKval == id:
                rv = getPartList([p], self.disk_profile)
                if rv and len(rv) == 1:
                    return True
        return False

    def isLV(self,id):
        for p in self.PartRecList:
            if p.PKval == id:
                rv = getLVList([p], self.disk_profile)
                if rv and len(rv) == 1:
                    return True
        return False

    def getNewPartId(self):
        if not self.PartRecList:
            return -1
        minid = 0
        for p in self.PartRecList:
            if p.PKval < minid:
                minid = p.PKval
        return minid-1

    def __str__(self):
        colLabels=['Device', 'Size(MB) ', 'Type  ', 'Mount Point   ']
        colWidths=[15,15,15,15]
        justification=[LEFT, RIGHT, LEFT, LEFT]

        txt = self.__createRowText(['a','b','c','d'], colWidths, justification)
        schema = self.schema
        str2display = ''

        lvg_keys = schema['vg_dict'].keys()

        for key in sorted(lvg_keys):
            lvg = schema['vg_dict'][key] 
            lvg_displayname = 'VG ' + key
            lvg_size_MB = ''
            # display volume groups first in listbox
            txt = self.__createRowText(['VG ' + key,  str(lvg_size_MB), 'VolGroup',
                                 ''], colWidths, justification)
            str2display += txt + '\n'

            lv_keys = lvg['lv_dict'].keys()
            for lv_key in sorted(lv_keys):
                lv =  lvg['lv_dict'][lv_key] 
                lv_devicename = '  LV ' + lv_key
                lv_size_MB = lv['size_MB']   
                # display indented logical volumes belonging to the vg.
                txt = self.__createRowText([lv_devicename, str(lv_size_MB),lv['fs'],
                                    lv['mountpoint']], colWidths, justification)
                str2display += txt + '\n'


        disk_keys = schema['disk_dict'].keys()
        for key in sorted(disk_keys):
            # display device
            device = schema['disk_dict'][key]
            txt = self.__createRowText(['Disk '+str(key),  '', '', ''], colWidths, justification ) 
            str2display += txt + '\n'

            parts_dict =  device['partition_dict']          
            parts_keys = parts_dict.keys()
            for part_key in sorted(parts_keys):
                partition = parts_dict[part_key]
                part_devicename = '  ' +'d'+ str(key) +'p'+ str(part_key)
                # indent one more level if logical partition.
                #if partition.part_type == 'logical': part_devicename = '  ' + part_devicename
                fs_type = partition['fs']
                mountpoint = partition['mountpoint']
                txt = self.__createRowText([part_devicename,
                                    str(partition['size_MB']),
                                    fs_type,
                                    mountpoint], colWidths, justification)
                str2display += txt + '\n'

        if str2display:
            str2display = self.__createRowText(colLabels, colWidths, justification)+\
                          '\n' + str2display

        return str2display


    def __createRowText(self, colTexts, colWidths, justification):
        if len(colWidths) is not len(colTexts):
            raise Exception, "Number of items in colWidths does not match \
                              number of items in colTexts."
        rowText = ''
        for i, text in enumerate(colTexts):
            if not text:
                text = ''
            currentColWidth = colWidths[i]
            currentColText = text[:currentColWidth]

            if justification[i] is LEFT:
                justifiedColText = ' ' + currentColText.ljust(currentColWidth-1)
            if justification[i] is CENTER:
                justifiedColText = currentColText.center(currentColWidth)
            if justification[i] is RIGHT:
                justifiedColText = currentColText.rjust(currentColWidth-1) + ' '

            rowText = rowText + justifiedColText
        return rowText

        


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
