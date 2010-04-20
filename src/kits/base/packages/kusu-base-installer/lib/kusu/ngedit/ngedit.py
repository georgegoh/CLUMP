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
import glob
import shutil
import time
try:
    import subprocess
except:
    from popen5 import subprocess
import tempfile
import path
import select
from UserDict import UserDict
from sets import Set
from xml.dom import minidom
from xml.dom.minidom import Node

from kusu.core.db import KusuDB
from kusu.nodefun import validateNodeFormat, seq2tplstr
from kusu.core.app import KusuApp
import kusu.util.log as kusulog
logger = kusulog.getPrimitiveLog()
logger.addFileHandler()

from kusu.util.tools import mkdtemp
from kusu.ngedit.constants import *
from kusu.util import rpmtool

# For TUI
from kusu.ui.text.USXscreenfactory import USXBaseScreen,ScreenFactory
from kusu.ui.text.USXnavigator import *
from kusu.ui.text import USXkusuwidgets as kusuwidgets

from primitive.system.software.dispatcher import Dispatcher
from kusu.util.cfm import runCfmMaintainerScripts, updateCfmPackages

MAXWIDTH = 70
MAXHEIGHT = 18
LEFT=kusuwidgets.LEFT
CENTER=kusuwidgets.CENTER
RIGHT=kusuwidgets.RIGHT

#emulate ternary cond. expression - only avail. in 2.5 & up :(
def ifelse(b, x, y): return ((b and [x]) or [y])[0]
# TODO: consolidate constants in one place
CFMBaseDir = "/etc/cfm"
PluginsDir = "/opt/kusu/lib/plugins/ngedit"
PluginsLibDir = PluginsDir + "/lib"
LockDir = "/var/lock/ngedit"

# TODO: initialize logging
kl = kusulog.getKusuLog()
if os.geteuid() == 0:
    kl.addFileHandler("/var/log/kusu/kusu-ngedit.log")
    kl = kusulog.getKusuLog('ngedit')
    kel = kusulog.getKusuEventLog()

class UnsupportedOSType(Exception):             pass
#NGE Exception hierarchy
class NodeGroupError(Exception):                pass
class NGEObjectException(NodeGroupError):       pass
class NGEDBException(NodeGroupError):           pass
class NGEInvalidRecord(NGEObjectException):     pass
class NGEPartSchemaError(NGEObjectException):   pass
class NGEDBReadFail(NGEDBException):            pass
class NGEDBWriteFail(NGEDBException):           pass
class NGEXMLParseError(Exception):              pass
class NGEValidationError(Exception):            pass
class NGECommitError(Exception):                pass
class NGEPartRemoveError(Exception):            pass

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
            query = 'INSERT into %s (%s) values (%s)' %\
                    (self.table, string.join(keylst,',') , string.join(vallst,','))

        try:
           kl.info(query)
           db.execute(query)
        except Exception,msg:
           raise NGEDBWriteFail,msg

        if mode == 'insert':
            #get the PK for the record just inserted
            try:
               if db.driver == 'mysql':
                  db.execute("SELECT last_insert_id()")
               else:
                  db.execute("SELECT last_value from %s_%s_seq" % (self.table,self.fields[0]))
               rv = db.fetchone()
               kl.info("the rv value is :%d len : %d, data = %s " % (rv[0], len(rv), self.data))
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


# Following data records are used to add/validate partitions
class DataRec:
    def __getitem__(self,field):
        return getattr(self,field)
    
    def __setitem__(self,field,val):
        setattr(self,field,val)
        
    def __str__(self):
        result = ''
        for field in self.__dict__.keys():
            if not (field.startswith('__') and field.endswith('__')):
                result = result + '%s = %s; ' % (field, self.__dict__[field])
                  
        return result

class PartDataRec(DataRec):
    idpartitions = None
    mntpnt = None
    fstype = None
    device = None
    size = None
    fill = None
    preserve = None

class LVDataRec(DataRec):
    idpartitions = None
    mntpnt = None
    fstype = None
    device = None
    size = None
    preserve = None    
    vol_group_id = None

class VGDataRec(DataRec):
    idpartitions = None
    device = None
    size = None
    phys_vols = []

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
        
        # Create partition schema when needed b/c it's expensive to create!
        self.PartSchema = None
        
        # Stores user's answers to interactive plug-in screens
        self.pluginDataDict = {}

        # Default behaviour is to run cfmsync
        self.cfmsync_required = True
        
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
            # we should sort partition instances by their partition ids before we update them into DB.
            self.data[link].sort(cmp=lambda x,y: x['idpartitions'] - y['idpartitions'])
            #special case - iterate over the list of PartitionRec instances
            for p in self.data[link]:   #for each partition
                p[p.PKfld] = None       #give the Partition record new identity
                p['ngid'] = self.PKval  #if copied from other N.G. - correct ngid field
                p.syncToDB(db)
                if db.driver == 'mysql' :
                   db.execute('select last_insert_id()') # revisit later for emulating this behaviour in postgres
                else:
                   #XXX hardcoded values here
                   db.execute("SELECT last_value from nodegroups_ngid_seq")
                rv = db.fetchone()
                p[p.PKfld] = rv[0]
        else:
            if link == 'modules': # special case for modules to respect loadorder column
                if db.driver == 'mysql':
                    query = "INSERT into %s (ngid, %s, loadorder) values " % (self.linksDBmap[link][0], \
                                                             self.linksDBmap[link][1])
                    query += "(%s, '%s', %s) " + ", (%s, '%s', %s)"*(len(self.data[link])-1)
                else: # postgres
                    query = "INSERT into %s (ngid, %s, loadorder)" % (self.linksDBmap[link][0], \
                                                             self.linksDBmap[link][1])
                    query+=" values (%s, '%s', %s); "
                    query = query*(len(self.data[link]))

                tpl = ()
                for i,v in enumerate(self.data[link]):
                    tpl += self.PKval, v, i + 1
                query = query % tpl

            else:
                if db.driver == 'mysql':
                    query = "INSERT into %s (ngid, %s) values " % (self.linksDBmap[link][0], \
                                                             self.linksDBmap[link][1])
                    query += "(%s, '%s') " + ", (%s, '%s')"*(len(self.data[link])-1)
                else: # postgres
                    query = "INSERT into %s (ngid, %s)" % (self.linksDBmap[link][0], \
                                                     self.linksDBmap[link][1])
                    query+=" values (%s, '%s'); " 
                    query = query*(len(self.data[link]))

                tpl = ()
                for v in self.data[link]:
                    tpl += self.PKval,v
                query = query % tpl

            try:
                kl.info(query)
                db.execute(query)
            except Exception,msg:
                raise NGEDBWriteFail,'Failed syncing link=%s to DB with msg = %s\nQuery=%s' %(link,str(msg),query)

    def __runSingleRowQuery(self, db, query):
        db.execute(query)
        rv = db.fetchone()
        return rv

    def __runMultiRowQuery(self, db, query):
        db.execute(query)
        rv = db.fetchall()
        return rv    
    
    def __str2IntForDict(self, val_dict,keys=()):
        for key in keys:
            if val_dict[key] and isinstance(val_dict[key],str):
                val_dict[key] = int(val_dict[key])

    def __str2IntForList(self, val_list):
        for i in xrange(0,len(val_list)):
            if val_list[i] and isinstance(val_list[i],str):
                val_list[i] = int(val_list[i])
    
    
    def initNullValues(self):
        #replace all Null values
        for f in NodeGroup.fields[1:]:
            if self[f] == None:
                self[f] = ''

        #if self['comps']:
        #    self['comps'] = [ int(x) for x in self['comps'] ]

        # Convert all IDs to integers
        self.__str2IntForDict(self.data,('ngid','repoid'))
        self.__str2IntForList(self.data['comps'])
        self.__str2IntForList(self.data['nets'])

        self.initNullPartValues(self['parts'])

    def initNullPartValues(self, partRecs):
        #work around Kusu bug 347
        if partRecs:
            for p in partRecs:
                if p['options'] == None:
                    p['options'] = ''
                if p['mntpnt'] == None:
                    p['mntpnt'] = ''
                if p['device'] == None:
                    p['device'] = ''        

    def updateNodegroupNetworks(self, mode, ngname, db=None, netids=None):
        ''' updates the nics table with entries '''
        
        from kusu.core.app import KusuApp
        from kusu.core.db import KusuDB
        from kusu.nodefun import NodeFun
        import kusu.ipfun

        node = NodeFun()
        ngid= node.getNodegroupByName(ngname)
        node.setNodegroupByID(ngid)

        if mode == NETWORKS_ADD:
           ipAddr = None
           interfaces = {}
           node._findInterfaces()

           preserveNodeIP = node._dbReadonly.getAppglobals('PRESERVE_NODE_IP')
           for myNode in node.getNodesFromNodegroup(ngid):
               ipAddr = None
               nid = node.getNodeID(myNode[0], skip_master=False)
               bootInterface = node.findBootDevice(myNode[0])
               myNodeInfo = node._nodegroupInterfaces
               interfaces.update(myNodeInfo)
               if bootInterface:
                   del interfaces[bootInterface]
               for nicdev in interfaces:
                   nodeInfo = node._nodegroupInterfaces[nicdev]
                   netid = nodeInfo['netid']

                   # Find out if the interface has an entry if so, ignore!
                   if node.nodeHasNICEntry(nid, netid):
                      continue

                   # Check length if returned tokens if its < 2 then its a DHCP network
                   #if len(Set(nodeInfo)) <= 3:
                   if nodeInfo['subnet'] == None and nodeInfo['gateway'] == None and nodeInfo['startip'] == None:
                      node._createNICBootEntry(nid, netid, False)
                      continue

                   macaddr = None
                   #try to use the preserved BMC IP if it's bmc nic in PRESERVE_NODE_IP mode
                   if nicdev.lower() == 'bmc' and preserveNodeIP == '1':
                       db.execute("SELECT mac FROM nics WHERE nid=%i AND boot=True" % nid)
                       try:
                           macaddr = db.fetchone()[0]
                           ipAddr = node.findOldBMCIPForNode(macaddr, ngid)
                       except:
                           pass

                   if ipAddr == None:
                      ipAddr = nodeInfo['startip'] # Initially starting IP only

                   IPincrement = nodeInfo['incr']
                   subnetNetwork = nodeInfo['subnet']

                   while True:
                      if not node.isIPUsed(ipAddr) and not node.isPreservedBMCIP(ipAddr, exclude_mac=macaddr):
                         node._addUsedIP(ipAddr)
                         node._cachedDeviceIPs[nicdev] = ipAddr
                         node._createNICBootEntry(nid, netid, 0, ipAddr)
                         ipAddr = None
                         break
                      ipAddr = kusu.ipfun.incrementIP(ipAddr, int(IPincrement), subnetNetwork)

        if mode == NETWORKS_REMOVE:
           for netid in netids:
               for nd in node.getNodesFromNodegroup(ngid):
                   nodeid = node.getNodeID(nd[0], skip_master=False)
                   try:
                       db.execute("DELETE FROM nics WHERE nid=%s AND netid=%s" % (nodeid, netid))
                   except:
                       pass   # There's nothing to delete

    def syncFromDB(self,db):
        ''' updates this instance with information from the database
        '''
        NodeGroupRec.syncFromDB(self,db)

        for l in self.links:
            self.__getLinkByFK(db,l)
            
        self.initNullValues()


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

        # Let's also erase from appglobals.
        try:
            db.execute("DELETE FROM appglobals WHERE ngid=%s" % self.PKval)
        except:
            kl.warn('Caught exception removing appglobals entries for nodegroup id %s' % self.PKval)

        NodeGroupRec.eraseFromDB(self,db)

    def copy(self):
        result = UserDict.copy(self)
        if result['parts']:
            result['parts'] = self.data['parts'][:] #copy the PartitionRec list
        if result['scripts']:
            result['scripts'] = self.data['scripts'][:] #copy the script list
        return result

    def validateGeneralInfo(self, db):
        '''Check if general parameters for node group are valid.
           Throws: NGEValidationError
        '''
        
        # validate ngid
        if not self.PKval:
            raise NGEValidationError, "Node Group ID must be specified."

        try:
            ngid = int(self.PKval)
        except ValueError:
            raise NGEValidationError, "Node Group ID '%s' must be a numerical value." % self.PKval

        query = "select ngid from nodegroups where ngid = %s" % self.PKval
        rv = self.__runSingleRowQuery(db, query)
        if not rv:
            raise NGEValidationError, "Specified Node Group is unknown."
 
        # Check for unmanaged node
        if ngid == db.getNgidOf('unmanaged'):
            raise NGEValidationError, "Operations on unmanaged node group are not allowed."

        # validate ngname
        ngname = self.data['ngname']
        if not ngname:
            raise NGEValidationError, "Node Group name is required."

        query = "select ngname from nodegroups where ngname = '%s' and ngid != %s" \
                    %(ngname, self.PKval)
        rv = self.__runSingleRowQuery(db, query)
        if rv:
            raise NGEValidationError, "Node Group name '%s' is already used." % ngname        

        # validate nameformat
        
        ## ensure nameformat is the same as the one in the DB 
        ## if the nodegroup has nodes
        
        nf = self.data['nameformat']
        query = "select nid from nodes where ngid = %s" % self.PKval
        db.execute(query)
        rv = db.fetchall()
        if len(rv) >= 1:
            query = "select nameformat from nodegroups where ngid = %s" % self.PKval
            db.execute(query)
            curNf = db.fetchone()[0]
            if not nf == curNf:
                raise NGEValidationError, "Name format for Node Group '%s' cannot be changed because " \
                    "it has >= 1 nodes." % ngname        

        ## validate nameformat syntax
        if not validateNodeFormat(nf):
            raise NGEValidationError, "Node group name format '%s' is invalid." % nf        

    def validateRepoInfo(self, db):
        '''Check if selected repository is valid.
           Throws: NGEValidationError
        '''
        
        # validate repo ID
        repoid = self.data['repoid']
        if not repoid:
            raise NGEValidationError, "A repository must be specified for a Node Group."
        
        try:
            int(repoid)
        except ValueError:
            raise NGEValidationError, "Repository ID '%s' must be a numerical value." % repoid 
        
        query = "select reponame from repos where repoid = %s" % repoid
        rv = self.__runSingleRowQuery(db, query)
        if not rv:
            raise NGEValidationError, "Specified repository is unknown."


    def validateBootInfo(self, db):
        '''Check if specified kernel and initrd files are valid.
           Throws: NGEValidationError
        '''
        # validate installtype
        installtype = self.data['installtype']
        if not installtype:
            raise NGEValidationError, "Install type is required for Node Group."       
 
        # validate kernel
        kernel = self.data['kernel']
        if installtype == 'multiboot':
            self.data['kernel'] = 'none'
        else:
            if not kernel:
                raise NGEValidationError, "A kernel file must be selected for a Node Group."

            BootDir = db.getAppglobals('PIXIE_ROOT')
            if not BootDir: BootDir = '/tftpboot/kusu'
            kernelpath = os.path.join(BootDir,kernel)
            if not os.path.exists(kernelpath):
                raise NGEValidationError, "Specified kernel file '%s' does not exist." % kernel

        # validate initrd 
        initrd = self.data['initrd']
        if installtype == 'multiboot':
            self.data['initrd'] = 'none'
        else:        
            if not initrd:
                raise NGEValidationError, "An initrd file must be selected for a Node Group."        
            BootDir = db.getAppglobals('PIXIE_ROOT')
            if not BootDir: BootDir = '/tftpboot/kusu'
            initrdpath = os.path.join(BootDir,initrd)
            if not os.path.exists(initrdpath):
                raise NGEValidationError, "Specified initrd file '%s' does not exist." % initrd

        # validate installtype
        installtype = self.data['installtype']
        if not installtype:  
            raise NGEValidationError, "Install type is required for Node Group."
        
        # validate type
        type = self.data['type']
        if not type:
            raise NGEValidationError, "Node type is required for Node Group."        
        
        
        # ensure that read-only fields (ngname, installtype, type) have not changed 
        
        query = "select ngname,installtype,type from nodegroups where ngid = %s" % self.PKval
        db.execute(query)
        (ngname,curInstType,curType) = db.fetchone()        
        
#         if not initrd == curInitrd:
#             raise NGEValidationError, "Initrd for Node Group '%s' cannot be changed." % ngname
        
        if not installtype == curInstType:
            raise NGEValidationError, "Install type for Node Group '%s' cannot be changed." % ngname
        
        if not type == curType:
            raise NGEValidationError, "Node type for Node Group '%s' cannot be changed." % ngname
         
        # Uncomment this code if we allow the user to change the initrd
        #initrdpath = os.path.join(BootDir,initrd)
        #if not os.path.exists(initrdpath):
        #    raise NGEValidationError, "Specified initrd file '%s' does not exist." % initrd
        

    def validateComponents(self, db):
        '''Check if all components selected are valid.
           Throws: NGEValidationError
        '''
        
        # validate each component ID
        cids = self.data['comps']
        
        for cid in cids:
            try:
                int(cid)
            except ValueError:
                raise NGEValidationError, "Component ID '%s' must be a numerical value." % cid
            
            query = "select cname from components where cid = %s" % cid
            rv = self.__runSingleRowQuery(db, query)
            if not rv:
                raise NGEValidationError, "Component with ID '%s' is unknown." % cid
    
    
    def validatePluginData(self, db):
        '''Check if user input for interactive plug-ins belonging to newly added
           components are valid. This method is only called when importing an XML 
           configuration file.
        '''
        # validate each component ID
        cids = self.data['comps']
        
        for cid in cids:
            
            # If component is not installed, and has interactive plug-ins then 
            # call the plug-in and validate the user's 
                        
            query = 'select cid from ng_has_comp where ngid = %s and cid = %s' % \
                        (self['ngid'],cid)
            rv = self.__runSingleRowQuery(db, query)
            
            if not rv:
                if self.__compHasInteractivePlugin(db, cid):
                    
                  #  compName = self.__getCompName(cid, db)
                  #  
                  #  # TODO: limited support for now; remove when we 
                  #  # complete Phase 2 of interactive plug-in project
                  #  supportedComps = ('component-LSF-Master-v7_0_2', 
                  #                    'component-LSF-Master-v7_0_4',
                  #                    'component-LSF-Compute-v7_0_2',
                  #                    'component-LSF-Compute-v7_0_4',
                  #                    'component-Platform-OFED-v1_3')
                  #  
                  #  if compName not in supportedComps:
                  #      raise NGEValidationError, "Component '%s' has an interactive " \
                  #          "plug-in which isn't yet supported." % compName
                    
                    pluginDataDict = {}
                    if self.pluginDataDict.has_key(cid):
                        pluginDataDict = self.pluginDataDict[cid]
                        
                    pluglibinst = self.__importPluginLib(cid, db, **pluginDataDict)
                    if not pluglibinst:
                        continue
                    (result, errMsg) = pluglibinst.validate()
                    if not result:
                        raise NGEValidationError, errMsg
    
    def validateNetworks(self, db):
        '''Check if networks selected are valid.
           Throws: NGEValidationError
        '''
        # validate each component ID
        netids = self.data['nets']
        devmap = {}
        
        for netid in netids:
            try:
                int(netid)
            except ValueError:
                raise NGEValidationError, "Network ID '%s' must be a numerical value." % netid
            
            query = "select device from networks where netid = %s" % netid
            rv = self.__runSingleRowQuery(db, query)
            if not rv:
                raise NGEValidationError, "Network with ID '%s' is unknown." % netid            

            # ensure duplicate devices are not selected
            device = rv[0]
            if device in devmap.values():
                raise NGEValidationError, \
                    "Multiple networks with the same device (%s) were selected." % device 
            else: 
                devmap[netid] = device

        # at least one provision network must be selected
        missing_provision_network = False
        if not netids:
            missing_provision_network = True
        else:
            query = ("select network from networks"
                     " where netid in %s and "
                     " (device like 'eth%%' or device like 'bond%%') and "
                     " type = 'provision'") % seq2tplstr(netids)
            rv = self.__runSingleRowQuery(db, query)
            if not rv:
                missing_provision_network = True

        if missing_provision_network:
            raise NGEValidationError, \
                    "At least one provision network with an ethernet (eth) interface must be selected."
    
    def validateModules(self, db):
        '''Check if all specified modules exist in the driverpacks from components
           selected for the node group.
           Throws: NGEValidationError
        '''
        
        # find the repository directory
        repoid = self.data['repoid']
        if not repoid:
            raise NGEValidationError, "A repository must be specified for the Node Group."

        from kusu.repoman import tools as rtool
        from kusu.core import database as sadb
        engine = os.getenv('KUSU_DB_ENGINE', 'postgres')
        dbinst = sadb.DB(engine, db='kusudb',username='nobody')
        
        # get the list of driverpacks to examine
        comps = self.data['comps']
        if not comps:
            raise NGEValidationError, "Node Group must have at least one component selected."
        
        query = "SELECT dpname from driverpacks where cid in " + seq2tplstr(comps)
        rv = self.__runMultiRowQuery(db, query)
        dpacklst = [ x for x, in rv]

        # Get list of modules from all driverpacks
        allmodules = []
        for dpack in dpacklst:
            try:
                dpackfull = rtool.getPackageFilePath(dbinst, repoid, dpack)
            except FileDoesNotExistError:
                raise NGEValidationError, 'Selected repository has an unknown OS type.'

            if os.path.exists(dpackfull):
                # Read contents of driverpack
                cmd = "rpm -qlp %s | grep '.ko$' | awk -F'/' '{print $NF}'" % dpackfull                 
                p = subprocess.Popen(cmd, shell=True,
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.PIPE)
                (stdout,stderr) = p.communicate()
                if p.returncode != 0:
                    raise NGEValidationError, "Could not get the module list from driver pack %s." % dpack
                
                newmodules = stdout.split('\n')
                newmodules = [x.split('.ko')[0] for x in newmodules ]
                allmodules.extend(newmodules)
                        
        # Determine if module is in any of the driverpacks
        for module in self.data['modules']:
            if module not in allmodules:
                raise NGEValidationError, "Module %s was not found in any driver packs for node group." % module
    
    def validatePackages(self, db):
        '''Check if all specified packages exist in the repository.
           Throws: NGEValidationError
        '''        
        
        # find the repository directory
        repoid = self.data['repoid']
        if not repoid:
            raise NGEValidationError, "A Repository must be specified for the Node Group."
        
        query = "select repository,ostype from repos where repoid = %s" % repoid
        (repodir,ostype) = self.__runSingleRowQuery(db, query)
        
        if not repodir:
            raise NGEValidationError, "Repository with ID '%s' is unknown." % repoid
        
        if not ostype:
            raise NGEValidationError, "Repository with ID '%s' does not have an OS type." % repoid
       
        from kusu.repoman import tools as rtool
        from kusu.core import database as sadb
        engine = os.getenv('KUSU_DB_ENGINE', 'postgres')
        dbinst = sadb.DB(engine, db='kusudb',username='nobody')

        repodirs = rtool.getPackagePath(dbinst, repoid)
        if not repodirs:
            raise NGEValidationError, 'Selected repository has an unknown OS type.'

        # validate all selected packages
        packages = self.data['packs']
        #Package name: <name>-<version>-<release>, version is usually like '3.1.6'
        #But some are tricky on SLES10SP3, for example iputils-ss021109-167.10.x86_64.rpm
        pkg_pattern = re.compile('^-[a-zA-Z]*[0-9]+')
        for pkg in packages:
            pkg_exists = False
            for repodir in repodirs:
                matches = glob.glob('%s/%s-*' % (repodir, pkg))
                matches = [os.path.basename(fn) for fn in matches]
                for fn in matches:
                    if pkg_pattern.match(fn[len(pkg):]):
                        pkg_exists = True
                        break
                if pkg_exists:
                    break
            if not pkg_exists:
                raise NGEValidationError, "Specified package '%s' was not found in the repository." % pkg
    
    
    def validateScripts(self, db):
        '''Check if all specified scripts exist.
           Throws: NGEValidationError
        '''
    
        destDir = db.getAppglobals('DEPOT_REPOS_SCRIPTS')
        if not destDir: destDir = '/depot/repos/custom_scripts'
        scripts = self.data['scripts']
        
        # Check if all of the scripts exist in the script repo
        for script in scripts:
            scriptPath = os.path.join(destDir,script)
            if not os.path.isfile(scriptPath):
                raise NGEValidationError, "Specified script '%s' does not exist in the repository." % script

    def createPartitionSchema(self):
        '''Create a new partition schema and populate it with the existing partition records 
           configured for the node group. This operation takes time to complete.'''
           
        if not self.PartSchema:
            #triggers disk_profile creation (slow!)
            self.PartSchema = PartSchema()
        
        if self.data['parts']:
            self.setPartitionSchemaWithRecs(self.data['parts'])
        else:
            self.setPartitionSchemaWithRecs([])
    
    def setPartitionSchema(self, PartSchema):
        '''Create a new schema using an existing schema'''
        self.PartSchema = PartSchema
    
    def setPartitionSchemaWithRecs(self, partRecList):
        '''Create a new schema using a list of partition records.
           Throws: NGEPartSchemaError
        '''
        if self.PartSchema:
            self.PartSchema.mycreateSchema(partRecList)
        else:
            raise NGEPartSchemaError, "Cannot set partitions for partition schema because schema does not exist."
    
    def getPartitionSchema(self):
        '''Get the current partition schema
           Throws: NGEPartSchemaError
        '''
        if self.PartSchema:
            return self.PartSchema
        else:
            raise NGEPartSchemaError, "Cannot get partition schema because schema does not exist."
    
    def editPartition(self, db, partDataRec):
        '''Create a new partition, or update an existing one in the 
           partition schema.
           Precondition: partDataRec has been validated by validatePartition()
           Throws: NGEPartSchemaError
        '''
        
        p = partDataRec
        
        id = p.idpartitions
        mntpnt = p.mntpnt
        device = p.device
        fill = p.fill
        preserve = p.preserve
        fs = p.fstype
        size = p.size

        if not self.PartSchema:
            raise NGEPartSchemaError, "Cannot add/edit partition because schema does not exist."

        try:
            id = int(id)
        except ValueError:
            id = None
        
        partition = self.PartSchema.getDictByPK(id)
        PartRec = self.PartSchema.getPartRecByPK(id)
        schema = self.PartSchema.schema
        
        # Partition ID not recognized...
        if not partition:
            # Look it up in the DB 
            query = "select idpartitions from partitions where idpartitions = %s" % id
            rv = self.__runSingleRowQuery(db, query)
            if not rv:
                # Not in DB, create new ID
                id = self.PartSchema.getNewPartId()
        
        # Create a partition record to add to the
        # our PartSchema object
        partrec = PartitionRec(idpartitions = id)
        
        partrec['mntpnt'] = mntpnt
        partrec['fstype'] = fs

        #options
        optlst = []
        if fs == 'physical volume':
            optlst.append('pv')
            if partition and PartRec:
                ispv,vgname = translatePartitionOptions(PartRec['options'], 'pv')
                if ispv and vgname:
                    optlst.append('vg=%s' %vgname)
        if fill == '1' or fill == 1:
            optlst.append('fill')
        optlst.sort()
        partrec['options'] = string.join(optlst,';')

        partrec['preserve'] = int(preserve)
        partrec['size'] = size


        # Determine partition number
        
        ## Spanning PV doesn't have a partition number
        if fs == 'physical volume' and (isinstance(device,str) and device.lower() == 'n'):
            partnum = 0       
        else:
            #determine the device num
            if device == None: #creating 1st partition
                device = 1
            else:
                device = int(device)
            
            #we're editing - get the disk_key we belong to
            currDiskNum = None
            currPartNum = None
            
            if partition:
                done = False
                for disk_key in schema['disk_dict']:
                    for part_key in schema['disk_dict'][disk_key]['partition_dict']:
                        part_dict = schema['disk_dict'][disk_key]['partition_dict'][part_key]
                        if part_dict['instid'] == id:
                            currDiskNum = disk_key
                            currPartNum = part_key
                            done = True
                            break
                    if done:
                        break         
            
            #determine the partition num
            if partition and device == currDiskNum:
                partnum = currPartNum        #preserve partition number
            else:
                #new disk or new partition
                try:
                    disk_dict = schema['disk_dict'][device]
                    part_keys = disk_dict['partition_dict'].keys()
                    part_keys = [ k for k in part_keys if not disk_dict['partition_dict'][k].has_key('pv_span') ]
                except KeyError:    #new disk
                    disk_dict = None
                    part_keys = []

                if not part_keys:
                    partnum = 1
                else:
                    partnum = max(part_keys) + 1
                    
        partrec['device'] = str(device)
        partrec['partition'] = str(partnum)
        partrec['ngid'] = int(self.data['ngid'])

        if partition:  #we're editing
            self.PartSchema.updatePartRec(partrec)
        else:   #new partition
            self.PartSchema.addPartRec(partrec)        
    
        # Must refresh schema after we update its partRecList
        self.PartSchema.mycreateSchema()    
    
    
    def editLV(self, db, lvDataRec):
        '''Create a new logical volume, or update an existing one in 
           the partition schema.
           Precondition: lvDatarec has been validated by validateLV()
           Throws: NGEPartSchemaError
        '''
        
        lv = lvDataRec
        
        id = lv.idpartitions
        lvname = lv.device
        fs = lv.fstype
        mntpnt = lv.mntpnt
        preserve = lv.preserve
        size = lv.size
        vg_id = lv.vol_group_id
        
        if not self.PartSchema:
            raise NGEPartSchemaError, "Cannot add/edit logical volumes because schema does not exist."        
        
        try:
            id = int(id)
        except ValueError:
            id = None
        
        partition = self.PartSchema.getDictByPK(id)
        PartRec = self.PartSchema.getPartRecByPK(id)
        schema = self.PartSchema.schema
        
        # Partition ID not recognized...
        if not partition:
            # Look it up in the DB 
            query = "select idpartitions from partitions where idpartitions = %s" % id
            rv = self.__runSingleRowQuery(db, query)
            if not rv:
                # Not in DB, create new ID
                id = self.PartSchema.getNewPartId()
        
        # Create a partition record to add to the
        # our PartSchema object
        partrec = PartitionRec(idpartitions = id)

        partrec['mntpnt'] = mntpnt
        partrec['fstype'] = fs
        
        # Options
        vg_id = int(vg_id)
        VG_PartRec = self.PartSchema.getPartRecByPK(vg_id)
        
        optlst = ['lv']
        optlst.append('vg=%s' % VG_PartRec['device'])
        if partition and partition['fill']:
            optlst.append('fill')
        partrec['options'] = string.join(optlst,';')

        # Preserve
        partrec['preserve'] = int(preserve)
        
        partrec['size'] = size        
        partrec['device'] = lvname
        partrec['ngid'] = int(self.data['ngid'])
        
        if partition: #we're editing
            self.PartSchema.updatePartRec(partrec)
        else:   #new partition
            self.PartSchema.addPartRec(partrec)

        # Must refresh schema after we update its partRecList
        self.PartSchema.mycreateSchema()    

    
    def editVG(self, db, vgDataRec):
        '''Create a new volume group, or update an existing one in 
           the partition schema.
           Precondition: vgDataRec has been validated by validateVG()
           Throws: NGEPartSchemaError
        '''
        
        vg = vgDataRec
        
        id = vg.idpartitions
        vgname = vg.device
        phys_vols = vg.phys_vols
        extent_size = vg.size
           
        if not self.PartSchema:
            raise NGEPartSchemaError, "Cannot add/edit volume groups because schema does not exist."           
                        
        try:
            id = int(id)
        except ValueError:
            id = None
                
        partition = self.PartSchema.getDictByPK(id)
        PartRec = self.PartSchema.getPartRecByPK(id)
        schema = self.PartSchema.schema
        
        # Partition ID not recognized...
        if not partition:
            # Look it up in the DB 
            query = "select idpartitions from partitions where idpartitions = %s" % id
            rv = self.__runSingleRowQuery(db, query)
            if not rv:
                # Not in DB, create new ID
                id = self.PartSchema.getNewPartId()
        
        # Create a partition record to add to the
        # our PartSchema object
        partrec = PartitionRec(idpartitions = id)
        
        oldAssocList = []
        if partition:
            PVidmap = self.PartSchema.getPVMap()
            oldAssocList = [k for k,v in PVidmap.items() if v and v == partition['name']]
        newAssocList = [int(x) for x in phys_vols]
        oldAssocSet = Set(oldAssocList)
        newAssocSet = Set(newAssocList)

        if partition and oldAssocSet == newAssocSet:
            #nothing has changed
            return
        
        for pv_id in oldAssocSet - newAssocSet:
            #handle removed associations
            p = self.PartSchema.getPartRecByPK(pv_id)
            optlst = p['options'].split(';')
            optlst = [x for x in optlst if not x.strip().lower().startswith('vg=')]
            optlst.sort()
            p['options'] = string.join(optlst, ';')

        for pv_id in newAssocSet - oldAssocSet:
            #handle added associations
            p = self.PartSchema.getPartRecByPK(pv_id)
            optlst = p['options'].split(';')
            optlst.append('vg=%s' %vgname)
            optlst.sort()
            p['options'] = string.join(optlst, ';')

        #options
        optlst = ['vg']
        optlst.append('extent=%sM' % extent_size)
        partrec['options'] = string.join(optlst, ';')

        # name
        partrec['device'] = vgname

        # preserve
        if partition:
            partrec['preserve'] = PartRec['preserve']
        else:
            partrec['preserve'] = 0     #does this have any effect?

        partrec['mntpnt'] = ''
        partrec['ngid'] = int(self.data['ngid'])

        if partition: #we're editing
            self.PartSchema.updatePartRec(partrec)
        else:   #new partition
            self.PartSchema.addPartRec(partrec)

        # Must refresh schema after we update its partRecList
        self.PartSchema.mycreateSchema()    

    
    def removePartition(self, db, id):
        '''Removes a partition from the partition schema given an ID.
           Throws: NGEPartRemoveError
                   NGEPartSchemaError
        '''

        if not self.PartSchema:
            raise NGEPartSchemaError, "Cannot remove partitions because schema does not exist."

        if not id:
            raise NGEPartRemoveError, "Delete operation requires a partition ID."
        
        selected_dict = self.PartSchema.pk2dict[id]
        if self.PartSchema.isPartition(id):
            if selected_dict['fs'] == 'physical volume':
                partrec = self.PartSchema.getPartRecByPK(id)
                (ispv, vg) = translatePartitionOptions(partrec['options'],'pv')
                if vg in self.PartSchema.schema['vg_dict'].keys():
                    #can't delete PV if any VGs are using it
                    raise NGEPartRemoveError, "Can't delete a PV if it has VGs using it."

        if self.PartSchema.isVG(id):
            #disallow deletion if LVs associated with this VG exist
            if selected_dict['lv_dict'].keys():
                raise NGEPartRemoveError, "Cannot delete a non-empty " + \
                                       "Volume group. Delete the logical volumes first."

            #disassociate the volume group from all physical volumes
            for disk_key in self.PartSchema.schema['disk_dict']:
                for part_key in self.PartSchema.schema['disk_dict'][disk_key]['partition_dict']:
                    part_dict = self.PartSchema.schema['disk_dict'][disk_key]['partition_dict'][part_key]
                    partrec = self.PartSchema.getPartRecByPK(part_dict['instid'])

                    #disassociate this PV
                    (ispv, vg) = translatePartitionOptions(partrec['options'],'pv')
                    if ispv and vg == selected_dict['name']:
                        optlst = partrec['options'].split(';')
                        #optlst = [ ifelse(x.strip().lower().startswith('vg='), 'vg=', x ) for x in optlst ]
                        optlst = [x for x in optlst if not x.strip().lower().startswith('vg=')]
                        partrec['options'] = string.join(optlst, ';')
                       
        self.PartSchema.delPartRec(id)
        self.PartSchema.mycreateSchema()

    def getIDsMountPoints(self, part_schema=None):
        '''Gets the instid, mount points used by partitions and logical volumes
           in the given partition schema dict
        '''
        if not part_schema:
            part_schema = self.PartSchema.schema

        loop1 = (part_schema['disk_dict'][disk]['partition_dict']
                     for disk in part_schema['disk_dict'])
        loop2 = ((part_dict[part]['instid'], part_dict[part]['mountpoint'])
                     for part_dict in loop1 for part in part_dict)
        part_mount_points = [(id, mnt_pnt) for (id, mnt_pnt) in loop2 if mnt_pnt]

        loop1 = (part_schema['vg_dict'][vg]['lv_dict']
                     for vg in part_schema['vg_dict'])
        loop2 = ((lv_dict[lv]['instid'], lv_dict[lv]['mountpoint'])
                     for lv_dict in loop1 for lv in lv_dict)
        lv_mount_points = [(id, mnt_pnt) for (id, mnt_pnt) in loop2 if mnt_pnt]

        return part_mount_points + lv_mount_points

    def validatePartition(self, db, partDataRec):
        '''Verifies parameters for a new partition added to the 
           partition schema.
           Throws: NGEValidationError
                   NGEPartSchemaError
        '''
        p = partDataRec
                
        id = p.idpartitions
        mntpnt = p.mntpnt
        device = p.device
        fill = p.fill
        preserve = p.preserve
        fs = p.fstype
        size = p.size

        if not self.PartSchema:
            raise NGEPartSchemaError,"Cannot validate partition because schema"\
                "does not exist."

        # Validate id
        try:
            id = int(id)
        except ValueError:
            raise NGEValidationError, "Partition ID '%s' must be an integer."\
                % id
                    
        # Validate fstype and mountpoint        
        if fs == "physical volume":
            if mntpnt:
                raise NGEValidationError, "A partition representing a physical "\
                    "volume cannot have a mountpoint."
        elif fs in ('ext2', 'ext3'):
            if not mntpnt:
                raise NGEValidationError, "A partition with ext2 or ext3 "\
                    "filesystem requires a mountpoint."

        # Validate mount point is unique
        if mntpnt:
            id_points = self.getIDsMountPoints()
            mount_points = [mnt_pnt for inst_id, mnt_pnt in id_points if inst_id != id]

            if mntpnt in mount_points:
                raise NGEValidationError, "Another logical volume or partition is "\
                      "already mounted at '%s'. Please use a different mount point" % mntpnt

        # Validate device

        if device == None:
            raise NGEValidationError, "A partition must be associated to a "\
                "disk or must be a spanning physical volume."
        
        if fs == "physical volume" and (isinstance(device,str) and 
                                        device.lower() == 'n'):
            ## Partition is a spanning PV
            pvmap = self.PartSchema.getPVMap()
            for k in pvmap.keys():
                p = self.PartSchema.getPartRecByPK(k)
                if p['device'] == 'N' and k != id:
                    raise NGEValidationError, "A spanning physical volume "\
                        "already exists."
        else:
            ## Partition is tied to one device
            try:
                device = int(device)
            except ValueError:
                raise NGEValidationError, "Partition device number '%s' must "\
                    "be a positive integer." % device
            
            disks = self.PartSchema.schema['disk_dict'].keys()
            
            # TODO - List of disks is generated from partition info.
            #If no partitions exist,
            # then new partitions are added to the first disk.
            if not disks and device != 1:
                raise NGEValidationError,"Partition device number is not valid."
             
            if disks and device not in disks:
                raise NGEValidationError,"Partition device number is not valid."


        # Validate size
        if size == None:
            raise NGEValidationError, "A size (in MB) must be specified for "\
                "a partition."
        
        msg = "The partition size must be a positive integer."
        try:
            size = int(size)
            if size <= 0:
                raise NGEValidationError, msg
        except ValueError:
            raise NGEValidationError, msg
        
        
        # Validate fill
        msg = "Partition fill option must be set to 0 or 1."
        try:
            fill = int(fill)
            if fill not in (0,1):
                raise NGEValidationError, msg 
        except (TypeError,ValueError):
            raise NGEValidationError, msg
        
        # Validate preserve
        msg = "Partition preserve option must be set to 0 or 1."
        try:
            preserve = int(preserve)
            if preserve not in (0,1):
                raise NGEValidationError, msg
        except (TypeError,ValueError):
            raise NGEValidationError, msg
        # we have added a new partition.
        # It can be a fill - if it is, then ensure it is the last.
        #For this, we must check if a partition has been filled prior
        # if so we must ask the user to delete it prior to creating this.
        # note that we have not performed the action yet
        newPartition = False
        if partDataRec.idpartitions not in\
               [x['idpartitions'] for x in self.PartSchema.PartRecList]:
            newPartition = True
        filtered_partlist = filter(lambda x: x['partition'] != None\
                                       ,self.PartSchema.PartRecList)
        filtered_partlist.sort(cmp=lambda x, y: x['idpartitions'] - y['idpartitions'])

        #new partition check - ensure we can only add a partition
        #if the disk has not been filled
        if newPartition:
            partlist  = filtered_partlist
            for part in partlist :
                if translatePartitionOptions(part['options'],'fill')[0]:
                    raise NGEValidationError,\
                        "A partition has already filled the entire disk.  "\
                        "Please re-configure partition %s mounted at %s before"\
                        " attempting to add new partitions"\
                        % (part['partition'] , part['mntpnt'])
         # its an update, we can only fill the last one
        if partDataRec.fill and not newPartition:
            if partDataRec.idpartitions != filtered_partlist[-1:][0].PKval:
                raise NGEValidationError,"You cannot fill a partition which is"\
                    " not the last, please delete subsequent partitions before"\
                    " trying to fill this."
        elif not newPartition :
            # double sanity check, even if we are not filling, just ensure 
            #that nothing has filled before. In the normal case we should
            # never be here. This can only happen if someone edits the DB
            partlist  = filtered_partlist[:-1]
            for part in partlist :
                if translatePartitionOptions(part['options'],'fill')[0]:
                    raise NGEValidationError, "A partition other than the "\
                        "last has filled the disk and a new partition has "\
                        "been inserted after.Partition schema is inconsistent!"\
                        " Delete and recreate this and partition "\
                        "%s mounted at %s to fix schema."\
                        % (part['partition'] , part['mntpnt'])

    def __validateLVName(self, name,LVedit=True):
        ''' This function is the python port of validate_name() in
        LVM 2.02 codebase. Function lib/misc/lvm-string.c : validate_name()
        It can also be used for LV Group names.
        '''

        if LVedit:
            typeName  = 'logical volume'
        else:
            typeName = 'logical volume group'
        if not name:
            return False,"A %s requires a name." % typeName
        if name[0] == '-':
            return False,' %s names cannot begin with a "-".' % typeName
        if name == '.' or name == '..':
            return False, ' %s names cannot be "." or ".."' % typeName
        found =  re.match(r'[a-zA-Z0-9_\-+]+$', name)
        if not found:
            return False,'Please enter a valid %s name' % typeName
        return True,None

    def validateLV(self, db, lvDataRec):
        '''Verifies parameters for a new logical volume added to the 
           partition schema.
           Throws: NGEValidationError
                   NGEPartSchemaError
        '''        
        
        lv = lvDataRec
        
        id = lv.idpartitions
        lvname = lv.device
        fs = lv.fstype
        mntpnt = lv.mntpnt
        preserve = lv.preserve
        size = lv.size
        vg_id = lv.vol_group_id

        if not self.PartSchema:
            raise NGEPartSchemaError, "Cannot validate logical volumes because schema does not exist."

        # Validate id
        try:
            id = int(id)
        except ValueError:
            raise NGEValidationError, "Logical volume ID '%s' must be an integer" % id
        # Validate name
        if not lvname:
            raise NGEValidationError, "A logical volume requires a name."
        retval, msg =  self.__validateLVName(lvname)
        # Validate first character of name is alpha numeric only.
        if not retval:
            raise NGEValidationError, msg
        # Validate fstype
        if fs in ('ext2','ext3') and not mntpnt:
            raise NGEValidationError, "Logical volume '%s' with filesystem ext2 or ext3 requires a mountpoint." %lvname

        # Validate mount point is unique
        if mntpnt:
            id_points = self.getIDsMountPoints()
            mount_points = [mnt_pnt for inst_id, mnt_pnt in id_points if inst_id != id]

            if mntpnt in mount_points:
                raise NGEValidationError, "Another logical volume or partition is "\
                      "already mounted at '%s'. Please use a different mount point" % mntpnt

        # Validate size
        if size == None:
            raise NGEValidationError, "A size (in MB) must be specified for a logical volume '%s'." %lvname
        try:
            size = int(size)
            if size <= 0:
                raise NGEValidationError, "Logical volume '%s' size must be a positive integer." %lvname
        except:
            raise NGEValidationError, "Logical volume '%s' size must be a positive integer." %lvname

        # Validate preserve
        try:
            preserve = int(preserve)
            if preserve not in (0,1):
                raise NGEValidationError, "Logical volume '%s' preserve option must be set to 0 or 1." %lvname
        except (TypeError,ValueError):
            raise NGEValidationError, "Logical volume '%s' preserve option must be set to 0 or 1." %lvname


        # Validate volume group ID
        if vg_id == None:
            raise NGEValidationError, "Logical volume '%s' must be assigned " %lvname + \
                "to a volume group. Ensure a volume group exists before creating logical volumes."
            
        try:
            vg_id = int(vg_id)
        except:
            raise NGEValidationError, "Logical volume '%s' refers to an invalid volume group." %lvname
        
        vg = self.PartSchema.getDictByPK(vg_id)
        if not vg:
            raise NGEValidationError, "Logical volume '%s' refers to an invalid volume group." %lvname

    
    def validateVG(self, db, vgDataRec):
        '''Verifies parameters for a new volume group added to the 
           partition schema.
           Throws: NGEValidationError
                   NGEPartSchemaError
        '''        
        
        vg = vgDataRec;
        
        id = vg.idpartitions
        vgname = vg.device
        phys_vols = vg.phys_vols
        extent_size = vg.size

        if not self.PartSchema:
            raise NGEPartSchemaError, "Cannot validate volume groups because schema does not exist."

        # Validate id
        try:
            id = int(id)
        except ValueError:
            raise NGEValidationError, "Volume group ID '%s' must be an integer." % id
                
        # Validate vg name
        if not vgname:
            raise NGEValidationError, "Volume group requires a name."
        retval, msg =  self.__validateLVName(vgname,LVedit=False)
        # Validate according to original LVM vg name requirements
        # see lvm2.02 lib/metadata/metadata.c:validate_new_vg_name()
        if not retval:
            raise NGEValidationError, msg
    
        vgdict = self.PartSchema.schema['vg_dict']
        if vgname in vgdict and vgdict[vgname]['instid'] != id:
            raise NGEValidationError, "Volume group name '%s' is already used." %vgname

        # Validate physical volumes assigned to VG
        if not phys_vols:
            raise NGEValidationError, "Volume group '%s' must use at least one physical volume." %vgname
        
        for pv_id in phys_vols:
            try:
                pv_id = int(pv_id)
            except:
                raise NGEValidationError, "Volume group '%s' refers to an invalid physical volume." %vgname 
            
            pv = self.PartSchema.getDictByPK(pv_id)
            if not pv:
                raise NGEValidationError, "Volume group '%s' refers to an invalid physical volume." %vgname
                        
        # Validate VG's extent size
        if extent_size == None:
            raise NGEValidationError, "An extent size (in MB) must be specified for volume group '%s'." %vgname        
        
        try:
            extent_size = int(extent_size)
            if extent_size <= 0:
                raise NGEValidationError, "Volume group '%s' extent size must be a positive integer." %vgname
        except:
            raise NGEValidationError, "Volume group '%s' extent size must be a positive integer." %vgname

    
    def summarizeChanges(self, db, prevNG):
        '''Returns a string that summarizes all of the node group 
           changes that will be made.'''        
        
        diffNG = self - prevNG
        kl.info("Finalize: diffNG = %s" %str(diffNG))
              
        msg = ''
        
        if not diffNG:
            msg += "No changes made to node group '%s'." % prevNG['ngname']
            return msg
        
        for field in NodeGroupRec.fields[2:] : #skip the keys
            if field in diffNG.keys():
                msg += "%s: \t%s\n" %(field.upper(),diffNG[field])

        if 'repoid' in diffNG.keys():
            query = '''SELECT reponame,repository,ostype from repos where
                       repoid = %s ''' % diffNG['repoid']
            db.execute(query)
            rv = db.fetchone()
            rv = [ ifelse(x==None,'',x) for x in rv ]
            msg += "REPO:\n\t| %s | %s | %s |\n" %tuple(rv)

        # go through comps, nets, packs, modules, scripts, parts
        if 'comps' in diffNG.keys():
            s1 = Set(ifelse(prevNG['comps'], [int(x) for x in prevNG['comps']], [] ))
            s2 = Set(ifelse(self['comps'], [int(x) for x in self['comps']], [] ))
            if 'repoid' in diffNG.keys():
                delItems = s1
                newItems = s2
            else:
                delItems = s1 - s2
                newItems = s2 - s1

            if delItems or newItems:
                msg += "COMPONENTS:\n"
            if delItems:
                query = "select cname from components where cid in %s" %seq2tplstr(list(delItems))
                db.execute(query)
                rv = db.fetchall()
                delItems = [x for x, in rv]
                tmpstr = string.join(['%s']*len(delItems), ', ')
                msg += "\t(-) " + tmpstr % tuple(sorted(delItems)) + '\n'
            if newItems:
                query = "select cname from components where cid in %s" %seq2tplstr(list(newItems))
                db.execute(query)
                rv = db.fetchall()
                newItems = [x for x, in rv]
                tmpstr = string.join(['%s']*len(newItems), ', ')
                msg += "\t(+) " + tmpstr % tuple(sorted(newItems)) + '\n'
            
        if 'nets' in diffNG.keys():
            netsstr = ''
            if diffNG['nets']:
                if len(diffNG['nets']) == 1:
                    tplstr = "(%s)" % int(diffNG['nets'][0])
                else:
                    tplstr = str(tuple([int(x) for x in diffNG['nets']]))
                if db.driver == 'mysql':
                   query = ''' select device,IFNULL(network, 'DHCP'),IFNULL(netname, '') from networks where
                netid in %s''' %tplstr

                else:
                   query = ''' select device,COALESCE(network, 'DHCP'),COALESCE(netname, '') from networks where
                netid in %s''' %tplstr
                db.execute(query)
                rv = db.fetchall()
                rv = [ ifelse(None in x, [ ifelse(y==None,'',y) for y in x ] , list(x)) for x in rv ]
                for record in rv:
                    netsstr += "\t| %s | %s | %s |\n" %tuple(record)
            msg += "NETWORKS SELECTED:\n%s\n" % netsstr
            
        caption = { 'packs': 'OPTIONAL PACKAGES',
                    'scripts': 'OPTIONAL SCRIPTS',
                    'modules': 'MODULES'
                  }

        for link in caption.keys():
            if link in diffNG.keys():
                s1 = Set(prevNG[link])
                s2 = Set(self[link])
                delItems = s1-s2
                newItems = s2-s1
                if delItems or newItems:
                    msg += caption[link] +':\n'
                if delItems:
                    tmpstr = string.join(['%s']*len(delItems), ', ')
                    msg += "\t(-) " + tmpstr % tuple(sorted(delItems)) + '\n'
                if newItems:
                    tmpstr = string.join(['%s']*len(newItems), ', ')
                    msg += "\t(+) " + tmpstr % tuple(sorted(newItems)) + '\n'

                #tmpstr = ''
                #if diffNG[link]: #one or more elements
                #    if link == 'scripts':
                #        #format scripts one per line
                #        tmpstr = '%s' + '\n\t%s'*(len(diffNG[link])-1)
                #    else:
                #        tmpstr = '%s' + ', %s'*(len(diffNG[link])-1)
                #    tmpstr = tmpstr % tuple(diffNG[link])
                #msg += "%s:\n\t%s\n" %(caption[link],tmpstr)

        if 'parts' in diffNG.keys() and self['installtype'] != 'diskless':
            msg += "PARTITIONS: schema changed\n"

        return msg

    def commitChanges(self, db, prevNG, kusuApp, windowInst):
        '''Commit any changes made to the node group.
           Params: prevNG          : NodeGroup object containing the original configuration
                   windowInst      : Instance of USXBaseScreen class. If None, then simply
                                     output to stdout
           Throws: NGECommitError
        '''
        
        ngname = self['ngname']
        eventStartMsg = "Committing changes for node group: %s" % ngname
        eventDoneMsg = "Finished committing changes for node group: %s" % ngname
        eventNoChangeMsg = "No changes committed for node group: %s" % ngname
        createEventFailMsg = \
            lambda(x): "Failed to commit changes for node group: %s. Error: %s" % (ngname,x)   
        
        # Event Start
        kel.info(eventStartMsg)
        
        diffNG = self - prevNG
        
        if not diffNG:
            kel.info(eventNoChangeMsg)
            CompIdList = self.__getCompIdList(db)
            self.__handleCompPlug(db, CompIdList, 'static', kusuApp, windowInst)
            if windowInst:
                del windowInst.selector.screens[-1]
            return
        else:   #only if there are changes
            #clean up partschema for diskless
            if self['installtype'] == 'diskless' and self['parts']:
                self['parts'] = []
                diffNG = self - prevNG

            #construct a diff NG object from dict
            diffNGobj = NodeGroup(**diffNG)
            diffNGobj['ngid'] = self['ngid']

            kl.debug('Finalize: self = %s' % str(self))
            kl.debug('Finalize: prevNG = %s' % str(prevNG))
            kl.debug('Finalize: diffNGobj = %s' % str(diffNGobj))
            
            db.beginTransaction()
            try:
                diffNGobj.syncToDB(db)
            except Exception,e:
                db.undoTransaction()
                msg = "DB Update failed: %s" % e
                kel.error(createEventFailMsg(msg))
                raise NGECommitError,msg

            db.endTransaction()
            
            #msg = "Database was successfully updated for node group '%s'" % self['ngname']
            #if windowInst:
            #    windowInst.selector.popupMsg("DB Update", msg)
            #else:
            #    sys.stdout.write(msg + "\n")

            # Add/remove nodes depending on network changes
            # If networks are deselected, delete nic entries associated for all nodes in selected nodegroup

            removeNets = (Set(prevNG['nets']) - Set(self['nets']))
            addNets = (Set(self['nets']) - Set(prevNG['nets']))

            if removeNets:
               self.updateNodegroupNetworks(NETWORKS_REMOVE, ngname, db, removeNets)
               os.system("echo '%s' > /etc/cfm/%s/etc/.updatenics" % (time.time(), ngname))

            if addNets:
               self.updateNodegroupNetworks(NETWORKS_ADD, ngname, db)
               os.system("echo '%s' > /etc/cfm/%s/etc/.updatenics" % (time.time(), ngname))

            #1. clean up scripts
            try:
                if 'scripts' in diffNG.keys():
                    delScripts = Set(prevNG['scripts']) - Set(self['scripts'])
                    if delScripts:
                        tplstr = "'%s'" + " , '%s'"*(len(delScripts)-1)
                        tplstr = tplstr % tuple(delScripts)
                        query = "select script from scripts where script in (%s)" % tplstr
                        db.execute(query)
                        rv = db.fetchall()
                        dbScripts = Set([x for x, in rv])   #scripts in use
                        delScripts -= dbScripts
                        for script in delScripts:
                            destDir = db.getAppglobals('DEPOT_REPOS_SCRIPTS')
                            if not destDir: destDir = '/depot/repos/custom_scripts'
                            delscr = os.path.join(destDir, script)
                            if os.path.isfile(delscr):
                                os.remove(delscr)
            except:
                #proceed despite cleanup failure
                kl.debug("Final Actions: script cleanup failed for ngname='%s'" %self['ngname'])
            else:
                kl.info("Final Actions: script cleanup succeeded for ngname='%s'" %self['ngname'])

            #2. clean up initrd
            try:
                if 'initrd' in diffNG.keys():
                    # retrieve the ostype which the nodegroup used to be associated with
                    from kusu.core import database as sadb
                    engine = os.getenv('KUSU_DB_ENGINE', 'postgres')
                    dbinst = sadb.DB(engine, db='kusudb',username='nobody')
                    prevOS = dbinst.Repos.selectone_by(repoid=int(prevNG['repoid'])).os
                    if prevOS:
                        prevOS_tup = (prevOS.name, prevOS.major, prevOS.minor, prevOS.arch)
                        # default initrd filename follows rule: "initrd-[osname]-[os.major].[os.minor]-[os.arch].img"
                        prevDefaultInitrd = "initrd-%s-%s.%s-%s.img" % prevOS_tup
                        # remove the previous initrd when the previous initrd is NOT the "default" one
                        # need to keep the default one for later nodegroup changing repos
                        if prevNG['initrd'] <> prevDefaultInitrd:
                            query = "select ngid from nodegroups where initrd = '%s'" % prevNG['initrd']
                            db.execute(query)
                            rv = db.fetchone()
                            BootDir = db.getAppglobals('PIXIE_ROOT')
                            if not BootDir: BootDir = '/tftpboot/kusu'
                            if not rv and os.path.isfile(os.path.join(BootDir, prevNG['initrd'])):
                                os.remove(os.path.join(BootDir, prevNG['initrd']))
            except:
                #proceed despite cleanup failure
                kl.debug("Final Actions: initrd cleanup failed for initrd='%s'" %prevNG['initrd'])
            else:
                kl.info("Final Actions: initrd cleanup succeeded for initrd='%s'" %prevNG['initrd'])

            #3. sync CFM dir name with NG name
            try:
                if 'ngname' in diffNG.keys():
                    srcNGcfmdir = os.path.join(CFMBaseDir,prevNG['ngname'])
                    dstNGcfmdir = os.path.join(CFMBaseDir,self['ngname'])
                    shutil.move(srcNGcfmdir, dstNGcfmdir)
            except:
                kl.debug("Final Actions: renaming of CFM directory failed for new NG name '%s'" % self['ngname'])
                msg = 'Failed to rename CFM directory from %s to %s.' \
                        % (prevNG['ngname'],self['ngname'])
                kel.error(createEventFailMsg(msg))
                raise NGECommitError,msg
            else:
                kl.info("Final Actions: renaming of CFM directory succeeded for new NG name '%s'" % self['ngname'])


            #4. handles nodegroup renaming case after the db sync-up is completely done
            if 'ngname' in diffNG.keys():
                self.__renameHandler(db, prevNG['ngname'], self['ngname'])
                kl.info("Final Actions: regenerating ICEintegration instconf xml file succeeded for new NG name %s" % self['ngname'])

            # finalizeCommit() was formerly formAction(). It can also 
            # throw NGECommitError.
            try:
                self.__finalizeCommit(db, prevNG, kusuApp, windowInst)
            except NGECommitError, e:
                kel.error(createEventFailMsg(e))
                raise

        # Event Start
        kel.info(eventDoneMsg)

    def hasChanged(self, prevNG):
        '''Returns true if the user has made changes to the node group'''
        diffNG = self - prevNG
        if diffNG:
            return True
        return False

    def syncNodesIsRequired(self, prevNG):
        '''Returns true if changes to current node group requires synchronizing
           nodes in node group. False otherwise.
        '''

        diffNG = self - prevNG
        key_lst = diffNG.keys()
        
        # Synchronize if packages or components were modified
        if ('packs' in key_lst or 'comps' in key_lst or 'nets' in key_lst or 'kparams' in key_lst):
            return True
        return False

    def syncNodes(self, windowInst, syncNG):
        '''Synchronize changes on all nodes in the node group.
           Params: windowInst      : Instance of USXBaseScreen class. If None, then simply
                                     output to stdout
                   syncNG          : Set to True to synchronize nodegroup, False otherwise
        '''
                
        # Run cfmsync
        if syncNG:
            self.__runTool('kusu-cfmsync', "-n '%s' -p -f" %self['ngname'], windowInst)
            if self['installtype'] == 'multiboot':
                self.__runTool('kusu-boothost', "-n '%s'" % self['ngname'], windowInst)            
        else:
            rmd = "kusu-cfmsync reminder"
            cmd = "kusu-cfmsync"+ " -n '%s' -p -f" %self['ngname']

            if self['installtype'] == 'multiboot':
                cmd = cmd + "\nkusu-boothost "+ "-n '%s'" % self['ngname']
                rmd = "kusu-boothost and "+ rmd
            
            if windowInst:
                windowInst.selector.popupMsg(rmd, "Please update the nodes manually"+\
                    " at your earliest convenience by running\n%s" %cmd)
            else:
                sys.stdout.write("Please update the nodes manually by running: %s\n" % cmd)

    def genKickstart(self,windowInst,generateKS):
        '''Generates kickstart file for nodes in the nodegroup and returns the string
        '''
                
        # Run genconfig
        db = windowInst.database # first detect target os
        repoid = self.data['repoid']
        query_start = 'select rname, version, arch from kits, repos_have_kits where ' +\
                      'repos_have_kits.repoid=%s and repos_have_kits.kid = kits.kid' % repoid
        if db.driver == 'mysql':
            query = query_start + ' and kits.isOS'
            db.execute(query)
        else: # postgres for now
            query = query_start + ' and kits."isOS"'
            db.execute(query, postgres_replace=False)
        
        full_os, ver, arch = db.fetchall()[0]
        os = re.compile('[a-z]+').findall(full_os)[0]
        target_os = (os, ver, arch)
        plugin = Dispatcher.get('inst_conf_plugin', os_tuple=target_os) # get os context plugin
        
        cmd = "kusu-genconfig %s %s" % (plugin, self.PKval)
        if generateKS:
            return self.__runTool('genconfig','%s %s' % ( plugin , self.PKval) ,windowInst)
        else:
            cmd = "kusu-genconfig %s %s" % (plugin, self.PKval)
            if windowInst:
                autoinst = windowInst.database.getAppglobals('DEPOT_AUTOINST_ROOT')
                windowInst.selector.popupMsg("kickstart reminder", "To update the nodes manually,"+\
                                                 " please run the command:\n%s >> %s/%s/kickstart.cfg\n" % (cmd, autoinst, self.PKval))
            else:
                sys.stdout.write("Please update the nodes manually by running: %s\n and saving the output to the kickstart.cfg location" % cmd)
                
        
#         try:
#             p = subprocess.Popen(cmd, shell=True,
#                                  stdout = subprocess.PIPE,
#                                  stderr = subprocess.PIPE)
#             (stdout,stderr) = p.communicate()
#         except OSError,e:
#             raise NGEValidationError, "Could not generate kickstart file from partition schema! : %s" % e
#         if p.returncode != 0:
#             raise NGEValidationError, "Could not generate kickstart file from partition schema! : %s" % stderr
#         return stdout

        

    def __compHasInteractivePlugin(self, db, compId):                
        plugcinst = self.__importPlugin(compId, db)
        if not plugcinst:
            return False
        return plugcinst.isInteractive()
    
    def __getPluginClz(self, plugdir, compName, pluginClzName, pluginBaseClz):
        CompPlugList = glob.glob('%s/*-%s.py' % (plugdir,compName))
        for plugfile in CompPlugList:
            plugmname = os.path.splitext(os.path.basename(plugfile))[0] # module name
            plugminst = __import__(plugmname)
            plugcname = getattr(plugminst, pluginClzName)
            if not issubclass(plugcname, pluginBaseClz):
                continue
            return plugcname
                
    def __importPlugin(self, compId, db):
        plugdir = PluginsDir
        if plugdir not in sys.path:
            sys.path.append(plugdir)        
        
        # Import plugin class
        compName = self.__getCompName(compId, db)
        plugcname = self.__getPluginClz(plugdir, compName, 'NGPlugin', NGEPluginBase)
        if plugcname:
            plugcinst = plugcname(db, KusuApp())
            return plugcinst
    
    def __importPluginLib(self, compId, db, **kwargs):
        plugdir = PluginsLibDir
        if plugdir not in sys.path:
            sys.path.append(plugdir)              
        
        # Import plugin class
        compName = self.__getCompName(compId, db)
        plugcname = self.__getPluginClz(plugdir, compName, 'NGPluginLib', NGPluginLibBase)
        if plugcname:
            pluglibinst = plugcname(db, KusuApp(), **kwargs)
            pluglibinst.setNodeGroupID(self['ngid'])
            pluglibinst.setComponentName(compName)
            pluglibinst.setBatchMode(True)
            return pluglibinst

    def __getCompName(self, compId, db):
        # Get component name
        query = 'select cname from components where cid = %s' % compId
        db.execute(query)
        #compName = db.fetchone()[0].lower()
        compName = db.fetchone()[0]
        return compName   

    def __getCompIdList(self, db):
        query = 'SELECT components.cid FROM components, ng_has_comp WHERE components.cid=ng_has_comp.cid AND ng_has_comp.ngid=%s' % self['ngid']
        db.execute(query)
        rv = db.fetchall()
        compIdList = [x for x, in rv]
        return compIdList         
        
    def __handleCompPlug(self, db, CompIdList, action, kusuApp, windowInst):
        
        plugdir = PluginsDir
        _msg = ""
        
        if not CompIdList:
            return
 
        CompIdList = [ int(x) for x in CompIdList ]

        PlugInstList_draw = []
        PlugInstList_run = []
        
        for compId in CompIdList:
            # Import plugin
            compName = self.__getCompName(compId, db)
            plugcinst = self.__importPlugin(compId, db)
            if not plugcinst:
                continue
            plugcinst.ngid = self['ngid']
            plugcinst.setComponentName(compName)
            
            if action == 'add':
                if plugcinst.isInteractive():
                    if windowInst:
                        # Interactive plug-in for TUI mode
                        PlugInstList_draw.append(plugcinst)
                    else:
                        # Interactive plug-in for batch mode
                        # 
                        # TODO: Rework this code during Phase 2 of interactive 
                        # plug-in project
                        
                        pluginDataDict = {}
                        if self.pluginDataDict.has_key(compId):
                            pluginDataDict = self.pluginDataDict[compId]    
                        pluglibinst = self.__importPluginLib(compId, db, **pluginDataDict)
                        if not pluglibinst:
                            continue
                        PlugInstList_run.append(pluglibinst)
                else:
                    PlugInstList_run.append(plugcinst)
            elif action == 'static':
                if plugcinst.isStatic():
                    if plugcinst.isInteractive():
                        if windowInst:
                            PlugInstList_draw.append(plugcinst)
                        else:
                            PlugInstList_run.append(plugcinst)
                    else:
                        PlugInstList_run.append(plugcinst)
            elif action == 'remove':
                PlugInstList_run.append(plugcinst)

            
        if action == 'add':
            #execute non-interactive first
            for inst in PlugInstList_run:
                try:
                    inst.add()
                except Exception,msg:
                    _msg += "The plugin for component " \
                            "'%s' failed. Error:\n%s" % (inst.getComponentName(), msg)
                    if windowInst:
                        windowInst.selector.popupMsg("Non-interactive component plugins", _msg)
                else:
                    _msg += "The plugin for component " \
                            "'%s' ran successfully.\n" % inst.getComponentName()
                
                if not windowInst:
                    sys.stdout.write(_msg + "\n")
                
            if windowInst:
                if PlugInstList_draw:
                    screenFactory = NGEScreenFactory(PlugInstList_draw)
                    ks = USXNavigator(screenFactory, screenTitle="Node Group Editor", showTrail=False)
                    ks.run()                                        
        elif action == 'static':
            for inst in PlugInstList_run:
                try:
                    inst.update(self)
                except Exception,msg:
                    _msg += "The plugin for component " \
                            "'%s' failed. Error:\n%s" % (inst.getComponentName(), msg)
                    if windowInst:
                        windowInst.selector.popupMsg("Non-interactive component plugins", _msg)
                else:
                    _msg += "The plugin for component " \
                            "'%s' ran successfully.\n" % inst.getComponentName()
                
                if not windowInst:
                    sys.stdout.write(_msg + "\n")
                
            if windowInst:
                if PlugInstList_draw:
                    screenFactory = NGEScreenFactory(PlugInstList_draw)
                    ks = USXNavigator(screenFactory, screenTitle="Node Group Editor", showTrail=False)
                    ks.run() 
        elif action == 'remove':
            for inst in PlugInstList_run:
                try:
                    inst.remove()
                except Exception,msg:
                    _msg += "The plugin for component " \
                            "'%s' failed. Error:\n%s" % (inst.getComponentName(), msg)
                    if windowInst:
                        windowInst.selector.popupMsg("Non-interactive component plugins", _msg)
                else:
                    _msg += "The plugin for component "\
                            "'%s' ran successfully.\n" % inst.getComponentName()

                if not windowInst:
                    sys.stdout.write(_msg + "\n")
                    
    def __importPluginGeneric(self, db):
        pluginGenericInstances = []
        pluginFileList = os.listdir(PluginsDir)
        pluginFileList.sort()  
        pluginList = []
 
        # Strip out files in the plugins directory with .pyc, ignore .swp files, and select only *-generic.py files. 
        for pluginName in pluginFileList:
             plugin, ext = os.path.splitext(pluginName)
             if ext == ".py":
                # Assumption generic plugin filename is of the form *-generic.py
                if plugin.endswith('generic') and not plugin[0] == '.':
                    pluginList.append(plugin)

        # Import the plugins
        moduleInstances = map(__import__, pluginList)
        
        # Create instances of each new plugin and store the instances.
        for thisModule in moduleInstances:
             try:
                 thisPlugin = thisModule.NGPlugin(db, KusuApp())
                 
                 pluginGenericInstances.append(thisPlugin)
             except:
                 self.stdoutMessage(kusuApp._("Warning: Invalid plugin '%s'. Does not have a NGPlugin class.\nThis plugin will be IGNORED.\n"),thisModule)
        return pluginGenericInstances 
 
    def handleGenericPlugins(self, db, prevNG, kusuApp, windowInst):
        
        plugdir = PluginsDir
        _msg = ""
        
        PlugInstList = []
        plugInstList = self.__importPluginGeneric(db)
        
        for plugcinst in plugInstList:
            plugcinst.ngid = self['ngid']
            try:
                plugcinst.finished(self, prevNG)
            except Exception,msg:
                _msg += "The generic plugin " \
                       "'%s' failed. Error:\n%s" % (plugcinst.getPluginName(), msg)
                if windowInst:
                    windowInst.selector.popupMsg("Non-interactive component plugins", _msg)
                else:
                    _msg += "The generic plugin " \
                            "'%s' ran successfully.\n" % plugcinst.getPluginName()
                
                if not windowInst:
                    sys.stdout.write(_msg + "\n")
                
    def __runTool(self,tool, argstr, windowInst):

        kl.info("Final Actions: Running %s:" %tool)
        cmd = "%s %s" %(tool,argstr)
        _msg = ""
        output = ""
        p = subprocess.Popen(cmd, shell=True,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.STDOUT
                            )
        if windowInst:
            prog_out = kusuwidgets.ProgressOutputWindow(windowInst.selector.mainScreen, \
                '%s progress' %tool, msg='',width=MAXWIDTH+3,height=MAXHEIGHT,scroll=0)
            
        t1 = time.time()

        while True:
            retval = p.poll()
            line = ''
            
            (rlist,wlist,xlist) = select.select([p.stdout.fileno()],[],[], 0.5)
            if rlist:
                line = p.stdout.readline()
                output += line
                if windowInst:
                    prog_out.setText(output)
                    prog_out.draw()
                    prog_out.refresh()
                else:
                    sys.stdout.write(line)
            
            if not line and retval != None:
                break

        if windowInst:
            prog_out.close()

        t2 = time.time()

        retcode = p.returncode

        if not retcode:
            _title = "%s - success" %tool
            _msg += "%s reported successful return.\n" %tool
        else:
            _title = "%s - error" %tool
            _msg += tool + " returned an error. The operation may be incomplete."  +\
                   " You can rerun the command manually as follows: %s\n" % cmd
        
        if windowInst:
            if tool != 'kusu-boothost':
                _msg += "\nPlease inspect the output below:\n"
                _msg += output
            windowInst.selector.popupMsg(_title, _msg, width = 60)
        else:
            sys.stdout.write(_msg)
            
        kl.info("%s finished in %f sec. Output:\n%s" %(tool, (t2-t1),output))
        return output #return output so this can be saved.

    # Check if the changes to be applied to the current nodegroup will expire or require
    # reinstallation of nodes
    def detectRisksInChanges(self, diffNG):

        expire_keys = []
        reinst = None
        expire = None
        diff_keys = Set(diffNG.keys())

        if diff_keys:
            reinst_keys = Set(['installtype', 'repoid', 'parts', 'modules',
                               'scripts', 'kernel', 'kparams'
                              ])
            expire_keys = reinst_keys | Set(['packs', 'comps'])
            reinst = diff_keys & reinst_keys
            expire = diff_keys & expire_keys

        return reinst, expire


    def __expireNodes(self, db, diffNG):

        (reinst, expire) = self.detectRisksInChanges(diffNG)

        update_vallst = []
        if reinst:
            update_vallst.append("bootfrom=False")
        if expire:
            update_vallst.append("state='Expired'")
            
        if update_vallst:
            query = "update nodes set " + string.join(update_vallst,',') + " where ngid = %s" %self.PKval
            try:
                db.execute(query)
            except:
                raise NGECommitError, "Failed to update the node states."

    def __renameHandler(self, db, prevNGName, curNGName):
        """
        After the nodegroup name change is synchronized to kusudb,
        handles the kickstart files under /opt/repository/instconfig
        and xml files under /opt/repository/.icle for the nodegroup 
        associated with the new name

        Parameters:
          db: kusudb connection
          prevNGName: the name of the nodegroup before the change
          curNGName: the name of the nodegroup after the change
        """

        if 'ice' == db.getAppglobals('PROVISION').lower():
            autoinst = db.getAppglobals('DEPOT_AUTOINST_ROOT')
            ngpath = os.path.join(autoinst, str(self['ngid']))
            if not os.path.exists(ngpath) : os.makedirs(ngpath)

            # convert ngnames to an ICE acceptable version
            r = re.compile('[^\w.-]')
            prevnname = r.sub('_', prevNGName)
            curnname = r.sub('_', curNGName)

            # remove the old kickstart file
            prevksfile = os.path.join(ngpath, '%s.cfg' % prevnname)
            if os.path.exists(prevksfile):
                os.unlink(prevksfile)

            # remove the old xml file
            icle_path = '/opt/repository/.icle'
            prevfilename = '%s/%s.xml' % (icle_path, prevnname)
            if os.path.exists(prevfilename):
                os.unlink(prevfilename)

            # regenerate the xml file
            os.system("kusu-genconfig ICEintegration instconf '%s' > %s/%s.xml" %  (curNGName, icle_path, curnname))

    def __finalizeCommit(self, db, prevNG, kusuApp, windowInst):
        
        diffNG = self - prevNG
        plugdir = PluginsDir

        #1. FinalActions: node state update
        self.__expireNodes(db, diffNG)

        #2. run second-party tools:
        # * if imaged (both disked & diskless)
        #        if changes in (components or packages or repo)
        #            run kusu-buildimage (kusu-buildimage -n $ngid)
        #  * if imaged (both disked & diskless)
        #        if changes in (modules or repo)
        #            kusu-buildinitrd -n $ngid
        #  * if package-based and adding a component with drivers
        #       kusu-driverpatch to patch initrd w/ new drivers
        #       kusu-driverpatch nodegroup id=self['ngid']

        key_lst = diffNG.keys()

        if self['installtype'] != 'package' and Set(key_lst) & Set(['modules','repoid','initrd']):
            #buildinitrd
            self.__runTool('kusu-buildinitrd', " -n '%s'" %self['ngname'], windowInst)

        if self['installtype'] != 'package' and Set(key_lst) & Set(['comps','packs','repoid','scripts']): 
            #buildimage
            self.__runTool("kusu-buildimage", " -n '%s'" %self['ngname'], windowInst)

        s1 = Set(self['comps'])
        s2 = Set(prevNG['comps'])
        addedComps = list(s1 - s2)
        removedComps = list(s2 - s1)
        addedComps = [int(x) for x in addedComps]
        if self['installtype'] == 'package' and addedComps:
            query = "select dpid from driverpacks where cid in %s" %seq2tplstr(addedComps)
            db.execute(query)
            rv = db.fetchall()
            if len(rv) >= 1:
                # Before running kusu-driverpatch, ensure we have the 'proper' initrd
                # Create a copy of the 'master' for this repo.
                db.execute('select ostype from repos where repoid = \'%s\'' % self['repoid'])
                rv = db.fetchall()                

                if rv:
                    BootDir = db.getAppglobals('PIXIE_ROOT')
                    if not BootDir: BootDir = '/tftpboot/kusu'
                    #srcInitrdFileName = os.path.join(BootDir, 'initrd-%s.img' % rv[0])
                    srcInitrdFileName = os.path.join(BootDir,self['initrd'])
                    dstInitrdFileName = os.path.join(BootDir, 'initrd.%s.%d.img' % ( self['installtype'], self['ngid'] ))

                    try:
                        shutil.copyfile(srcInitrdFileName, dstInitrdFileName)
                    except OSError, e:
                        _title = "Error copying initrd"
                        _msg = "Error copying pristine initrd (%s to %s) for this nodegroup. " \
                               "This failure will likely result in unexpected behaviour. Error: %s" \
                            % ( srcInitrdFileName, dstInitrdFileName, e )
                        if windowInst:
                            windowInst.selector.popupMsg(_title, _msg)
                        else:
                            sys.stdout.write(_msg)
                else:
                    _title = "Error determining initrd for nodegroup"
                    _msg = "Error determining the initrd for the nodegroup. " \
                           "This nodegroup appears not to have an associated repo.  Using defaults."
                    if windowInst:
                        windowInst.selector.popupMsg(_title, _msg)
                    else:
                        sys.stdout.write(_msg)                        

                #driverpatch
                self.__runTool('kusu-driverpatch', " nodegroup name='%s'" %self['ngname'], windowInst)

        #3. Run any CFM maintainer scripts found in 
        #   {DEPOT_KITS_ROOT}/<kid>/cfm/*.rc.py
        runCfmMaintainerScripts()
            
        #4. handle component plugins
        if plugdir not in sys.path:
            sys.path.append(plugdir)

        self.__handleCompPlug(db, removedComps, 'remove', kusuApp, windowInst)
        self.__handleCompPlug(db, addedComps, 'add', kusuApp, windowInst)

        #Please be carefull for writing NGEDIT static plugins: 
        # method update() won't be called during adding/removing components, please call update() 
        # in add() or remove() if you also want update() to be called in these situations.
        CompIdList = self.__getCompIdList(db)
        staticComps = [id for id in CompIdList if (id not in addedComps and id not in removedComps)]
        self.__handleCompPlug(db, staticComps, 'static', kusuApp, windowInst)

        #5. show cfmsync screen only if packages or components
        # were modified for node group
        if not self.syncNodesIsRequired(prevNG) and windowInst:
            self.cfmsync_required = False
        
        key_lst = diffNG.keys()
        # Synchronize if packages or components were modified
        if ('packs' in key_lst or 'comps' in key_lst):
            updateCfmPackages(self.data['ngname'])

# NodeGroup record using XML-based data 
class NodeGroupXMLRecord(NodeGroup):
    
    def __init__(self, record=None, **kwargs):
        NodeGroup.__init__(self, record, **kwargs)
    
    def __isElement(self,el):
        return el and el.nodeType == Node.ELEMENT_NODE
   
    def __getName(self,el):
        return el and el.nodeName
    
    def __getValue(self,el):
        if el and el.firstChild and el.firstChild.nodeType == Node.TEXT_NODE:
            return str(el.firstChild.nodeValue).strip()
        else:
            return None
    
    def __getAttr(self,el,attr):
        return el and str(el.getAttribute(attr))
        
    def __readSingleValuesFromSection(self, section, val_dict, fields=(), ignoredFields=()):
        for el in [x for x in section.childNodes if self.__isElement(x)]:
            name = self.__getName(el)
            if name in fields:
                val_dict[name] = self.__getValue(el)
            elif name in ignoredFields:
                pass
            else:
                raise NGEXMLParseError, "Unrecognized tag <%s> found in XML file." % name  
    
    def __readMultiValuesFromSection(self, section, val_dict, tag, subTag):
        val_dict[tag] = []
                
        for el in [x for x in section.childNodes if self.__isElement(x)]:
            name = self.__getName(el)
            if name == subTag:
                val_dict[tag].append(self.__getValue(el))
            else:
                raise NGEXMLParseError, "Unrecognized tag <%s> found in XML file." % name  
    
    def __readScriptsSection(self, section):
        self.data['scripts'] = []
        newScriptPaths = []
        
        for el in [x for x in section.childNodes if self.__isElement(x)]:
            name = self.__getName(el)
            if name == 'script':
                # Keep track of the script paths 
                script = self.__getValue(el)
                srcdir = self.__getAttr(el,'srcdir')
                if srcdir:
                    newScriptPaths.append(os.path.join(srcdir,script))
                
                self.data['scripts'].append(script)
            else:
                raise NGEXMLParseError, "Unrecognized tag <%s> found in XML file." % name
        
        return newScriptPaths
        
    
    def __readPartitionSchema(self, section):
    
        # Returns a dictionary which is can be used to convert
        # to other data structures like PartSchema:
        #    part_list => list of PartDataRec objects
        #    lv_list => list of LVDataRec objects
        #    vg_list => list of VGDataRec objects
        
        schemaDict = {'part_list':[], 'lv_list':[], 'vg_list':[]}
        
        partTags = [x for x in section.childNodes if self.__isElement(x)]
        
        for el in partTags:
            name = self.__getName(el)
            
            if name == 'partition':
                rec = PartDataRec()
                tagsToParse = ('idpartitions', 'device', 'mntpnt',
                               'fstype', 'size', 'preserve','fill')
                tagsToIgnore = ()
                recList = schemaDict['part_list']
            elif name == 'log_vol':
                rec = LVDataRec()
                tagsToParse = ('idpartitions', 'device', 'mntpnt',
                               'fstype', 'size', 'preserve','vol_group_id')
                tagsToIgnore = ()
                recList = schemaDict['lv_list']
            elif name == 'vol_group':
                rec = VGDataRec()
                tagsToParse = ('idpartitions', 'device', 'size','preserve')
                tagsToIgnore = ('phys_vols',)
                recList = schemaDict['vg_list']
                
                # Get the physical volumes assigned to the volume group
                physVolsTags = el.getElementsByTagName('phys_vols')
                if len(physVolsTags) == 1:
                    self.__readMultiValuesFromSection(physVolsTags[0], rec, 'phys_vols', 'id')
                elif len(physVolsTags) > 1:
                    raise NGEXMLParseError, "Cannot have more than one <phys_vols> tag for a volume group"
            else:
                pass
                                 
            self.__readSingleValuesFromSection(el, rec, tagsToParse, tagsToIgnore)
            
            # TODO -- Some functions assume mntpnt is always string. Always initialize it
            # to empty string.
            if hasattr(rec, 'mntpnt'):
                if not rec.mntpnt: rec.mntpnt = ''
            
            recList.append(rec)
        
        return schemaDict
    
    def __readPluginData(self, section):
        # Read user's answers to interactive plug-in screen and
        # save them in a dictionary:
        #         self.pluginDataDict[component id][data id] = <data>
        #    e.g. self.pluginDataDict[83]['license_accepted'] = true
        
        result = {}
        compTags = [x for x in section.childNodes if self.__isElement(x)]
        
        for compEl in compTags:
            try:
                compid = int(self.__getAttr(compEl, 'id'))
                result[compid] = {}
            except ValueError:
                continue
            
            dataTags = [x for x in compEl.childNodes if self.__isElement(x)]
            for dataEl in dataTags:
                dataid = self.__getAttr(dataEl, 'id')
                dataval = self.__getAttr(dataEl, 'value')
                result[compid][dataid] = dataval
                
        self.pluginDataDict = result
    
    # For creating an XML section tag with multiple sub-tags having different names
    def __createXMLSectionWithDict(self, xml, sectionTag, val_dict, keys):
        sectionEl = xml.createElement(sectionTag)
        for key in keys:
            sectionEl.appendChild(self.__createXMLElement(xml,key,val_dict[key]))
        return sectionEl

    # For creating an XML section tag with multiple sub-tags having the same name
    def __createXMLSectionWithList(self, xml, sectionTag, subTag, val_list):
        sectionEl = xml.createElement(sectionTag)
        for val in val_list:
            sectionEl.appendChild(self.__createXMLElement(xml,subTag,val))
        return sectionEl
    
    # For creating a simple XML tag with a single value
    def __createXMLElement(self, xml, elementTag, val):
        singleEl = xml.createElement(elementTag)
        textEl = xml.createTextNode(str(val))
        singleEl.appendChild(textEl)
        return singleEl

    def __createXMLForPartition(self, part_rec, xml, pk):
        curr_section = self.__createXMLSectionWithDict(
                    xml, "partition", part_rec,
                    ("idpartitions", "mntpnt", "fstype", "device", "size"))

        # Get the fill option
        fill = translatePartitionOptions(part_rec['options'], 'fill')[0]
        fill = fill and 1 or 0
        curr_section.appendChild(self.__createXMLElement(xml, "fill", fill))
        # Get the preserve column
        preserve = part_rec['preserve'] and 1 or 0
        curr_section.appendChild(self.__createXMLElement(xml, "preserve", preserve))

        return curr_section


    # For creating partition schema XML section
    def __createXMLPartSection(self, xml, PartSchema):
        sectionEl = xml.createElement("partition_schema")
        pk_list = sorted(PartSchema.pk2dict.keys())
        pk_fill = None
        for pk in pk_list:
            part_rec = PartSchema.getPartRecByPK(pk)
            curr_section = None
            if PartSchema.isPartition(pk):
                # Check the fill option. Put the mountpoint partition that is set to 'Fill at least' as the last of 
                # the partition schema section in the XML file. There will only be 1 partition set to 'Fill at least'
                fill = translatePartitionOptions(part_rec['options'], 'fill')[0]
                if fill:
                    pk_fill = pk
                else:
                    curr_section=self.__createXMLForPartition(part_rec, xml, pk)

            elif PartSchema.isVG(pk):
                curr_section = self.__createXMLSectionWithDict(
                    xml, "vol_group", part_rec, ("idpartitions","device"))

                # Get the VG extent size 
                vg_extent_size = translatePartitionOptions(part_rec['options'], 'vg')[1]
                ## Remove the trailing "M" 
                vg_extent_size = vg_extent_size[:-1]
                curr_section.appendChild(
                    self.__createXMLElement(xml, "size", vg_extent_size))

                # Get the PV's attached to this VG
                pvmap = PartSchema.getPVMap()
                pvlist = []
                for k in pvmap.keys():
                    if pvmap[k] == part_rec["device"]:
                        pvlist.append(k)
                curr_section.appendChild(
                    self.__createXMLSectionWithList(xml, "phys_vols", "id", pvlist))

            elif PartSchema.isLV(pk):
                curr_section = self.__createXMLSectionWithDict(
                    xml, "log_vol", part_rec,
                    ("idpartitions", "mntpnt", "fstype", "device", "size"))

                # Get the VG ID
                vg_name = translatePartitionOptions(part_rec['options'],'lv')[1]
                vg_id = None
                for curr_vg_name in PartSchema.schema['vg_dict'].keys():
                    if curr_vg_name == vg_name:
                        vg_id = PartSchema.schema['vg_dict'][curr_vg_name]['instid']
                        break

                curr_section.appendChild(self.__createXMLElement(xml, "vol_group_id", vg_id))
                # Get the preserve column
                preserve = part_rec['preserve'] and 1 or 0
                curr_section.appendChild(self.__createXMLElement(xml, "preserve", preserve))

            else:
                continue

            if curr_section:
                sectionEl.appendChild(curr_section)

        if pk_fill:
            part_rec = PartSchema.getPartRecByPK(pk_fill)
            curr_section=self.__createXMLForPartition(part_rec, xml, pk_fill)
            sectionEl.appendChild(curr_section)

        return sectionEl

    
    def syncFromDBAndDump2XML(self, db):
        '''Returns a string containing the XML representation of 
        the node group after synchronizing with the DB.'''
        
        self.syncFromDB(db)
        
        xml = minidom.Document()
        root = xml.createElement("ngedit")        
        
        # Create <general_info>
        general_info = self.__createXMLSectionWithDict(
                xml, "general_info", self, ('ngid','ngname','ngdesc','nameformat'))
        root.appendChild(general_info)
        
        # Create <repository>
        repository = self.__createXMLSectionWithDict(
                xml, "repository", self, ('repoid',))
        root.appendChild(repository)
        
        # Create <boot_params>
        boot_params = self.__createXMLSectionWithDict(
                xml, "boot_params", self, 
                ('kernel','kparams','initrd','installtype','type'))
        root.appendChild(boot_params)
        
        # Create <components>
        components = self.__createXMLSectionWithList(
                xml, "components", "cid", self.data['comps'])        
        root.appendChild(components)
        
        # Create <networks>
        networks = self.__createXMLSectionWithList(
                xml, "networks", "netid", self.data['nets'])
        root.appendChild(networks)
        
        # Create <optional_pkgs>
        optional_pkgs = self.__createXMLSectionWithList(
                xml, "optional_pkgs", "packagename", self.data['packs'])
        root.appendChild(optional_pkgs)
        
        # Create <custom_scripts>
        custom_scripts = self.__createXMLSectionWithList(
                xml, "custom_scripts", "script", self.data['scripts'])
        root.appendChild(custom_scripts)
        
        # Create <modules>
        modules = self.__createXMLSectionWithList(
                xml, "modules", "module", self.data['modules'])
        root.appendChild(modules)
        
        # Create <partition_schema>
        NodeGroup.createPartitionSchema(self)
        partition_schema = self.__createXMLPartSection(xml, self.PartSchema)
        root.appendChild(partition_schema)

        
        xml.appendChild(root)
        return xml.toprettyxml()

    
    def getNGNameFromXMLFile(self, xmlFilePath):
        '''Returns the node group name found in the specified XML 
           configuration file. 
        '''
        
        # Parse the XML File
        
        if not os.path.exists(xmlFilePath):
            raise NGEXMLParseError, "Cannot read XML file because it does not exist."
        
        try:
            doc = minidom.parse(xmlFilePath)
        except:
            raise NGEXMLParseError, "Cannot read XML file because it is not well-formed."
    
        tags = doc.getElementsByTagName('ngname')
        if not tags:
            raise NGEXMLParseError, "Cannot find node group name in the XML file."
        
        ngname = self.__getValue(tags[0])
        return ngname
    
    
    def processXMLFile(self, xmlFilePath, db, testMode=False):
        '''Parses the XML configuration file and validates the contents.
           Throws: NGEXMLParseError if XML parsing error occurred
                 : NGEValidationError if validation error occurred
        '''
        
        # Parse the XML File
        
        if not os.path.exists(xmlFilePath):
            raise NGEXMLParseError, "Cannot read XML file because it does not exist."
        
        try:
            doc = minidom.parse(xmlFilePath)
        except:
            raise NGEXMLParseError, "Cannot read XML file because it is not well-formed."       
                
        root = doc.firstChild
        if not root:
            raise NGEXMLParseError, "Cannot find root element for XML file."
        ng_sections = root.childNodes
        
        # Read data from all sections in the XML file
        
        newScriptPaths = []
        schemaDict = {}
        
        for section in [x for x in ng_sections if self.__isElement(x)]:

            section_name = self.__getName(section)
            
            # <general_info> section
            if section_name == "general_info":
                self.__readSingleValuesFromSection(section, self.data, 
                    ('ngid','ngname','ngdesc','nameformat'))
                
            # <repository>
            elif section_name == "repository":
                self.__readSingleValuesFromSection(section, self.data, ('repoid',))
          
            # <boot_params>
            elif section_name == "boot_params":
                self.__readSingleValuesFromSection(section, self.data, 
                    ('kernel', 'kparams', 'initrd', 'installtype', 'type'))
 
            # <components>
            elif section_name == "components":
                self.__readMultiValuesFromSection(section, self.data, 'comps',
                                                self.linksDBmap['comps'][1])
 
            # <networks>
            elif section_name == "networks":
                self.__readMultiValuesFromSection(section, self.data, 'nets',
                                                self.linksDBmap['nets'][1]) 
 
            # <optional_pkgs>
            elif section_name == "optional_pkgs":
                self.__readMultiValuesFromSection(section, self.data, 'packs',
                                                self.linksDBmap['packs'][1])              
 
            # <custom_scripts>
            elif section_name == "custom_scripts":
                newScriptPaths = self.__readScriptsSection(section)
 
            # <modules>
            elif section_name == "modules":
                self.__readMultiValuesFromSection(section, self.data, 'modules',
                                                self.linksDBmap['modules'][1])
 
            # <partition_schema>
            elif section_name == "partition_schema":
                schemaDict = self.__readPartitionSchema(section)
        
            # <plugin-data>
            elif section_name == "plugin-data":
                self.__readPluginData(section)
        
            # unrecognized tag
            else:
                raise NGEXMLParseError, "Unrecognized tag <%s> found in XML file." % section_name
        
                
        NodeGroup.initNullValues(self)
        
        # Validate the fields
        validators = (NodeGroup.validateGeneralInfo, 
                      NodeGroup.validateRepoInfo,
                      NodeGroup.validateBootInfo,
                      NodeGroup.validateComponents,
                      NodeGroup.validateNetworks,
                      NodeGroup.validatePackages,
                      NodeGroup.validatePluginData)
        
        for validator in validators:
            validator(self,db) 
        
        # Validate scripts
        # Copy over new script before validating.
        copiedScripts = copyScripts(db, newScriptPaths)

        try:
            NodeGroup.validateScripts(self, db)
        except NGEValidationError:
            delScripts(db, copiedScripts)
            raise

        # Remove any copied scripts in test mode
        if testMode:
            delScripts(db, copiedScripts)

        # Validate modules
        # for imaged or diskless node groups
        if self.data['installtype'] in ('disked','diskless'):
            NodeGroup.validateModules(self,db)            
        
        # Validate each partition before adding it to the 
        # schema. This step applies to only 
        # package-based or imaged node groups.
                
        if self.data['installtype'] not in ('package','disked'):
            self.data['parts'] = []
            
        else:
        
            # Create an empty partition schema
            NodeGroup.createPartitionSchema(self)
        
            # We must first import hidden partition entries  
            # into the schema (if they exist)
            hiddenRecs = []
            query = "select * from partitions where ngid = %s " % self.data['ngid'] + \
                    "and (options like 'partitionID=%' or options like 'preserveDefault=%')"
            
            db.execute(query)
            rv = db.fetchall()

            if rv:
                for row in rv:
                    part_rec = PartitionRec(idpartitions = row[0])
                    part_rec.set(part_rec.fields[1:], row[1:])
                
                    hiddenRecs.append(part_rec)
        
                NodeGroup.initNullPartValues(self, hiddenRecs)
                self.PartSchema.mycreateSchema(hiddenRecs)
            
            # Add all partitions first
            for partDataRec in schemaDict['part_list']:
                NodeGroup.validatePartition(self, db, partDataRec)                
                NodeGroup.editPartition(self, db, partDataRec)
            
            # Then add volume groups
            for vgDataRec in schemaDict['vg_list']:
                NodeGroup.validateVG(self, db, vgDataRec)
                NodeGroup.editVG(self, db, vgDataRec)
            
            # Then add logical volumes
            for lvDataRec in schemaDict['lv_list']:
                NodeGroup.validateLV(self, db, lvDataRec)
                NodeGroup.editLV(self, db, lvDataRec)                
            
            # Save partition records...
            self.data['parts'] = self.PartSchema.PartRecList                    
            kl.debug("Partition list: %s" % self.data['parts'])


def RpmNameSplit(packname):
    ''' return a tuple (name,version,release,arch,ext)
    '''
    rv = ['','','','','']
    try:
        nvr,rv[3],rv[4] = packname.rsplit('.',2)
        rv[0:2] = nvr.rsplit('-',2)
    except:
        try:
            rpmpack = rpmtool.RPM(str(packname))
            name = rpmpack.getName()
            version = rpmpack.getVersion()
            release = rpmpack.getRelease()
            arch = rpmpack.getArch()
            ext = 'rpm'
            rv = [name, version, release, arch, ext]
        except:
            pass
    return tuple(rv)

def nxor(*args):
    """nxor(varargs args)
    N-way function, only one condition may be true otherwise false. """
    return len([x for x in args if x]) == 1

from kusu.ngedit.partition import *
from primitive.system.hardware.partitiontool import DiskProfile

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
            self.disk_profile = DiskProfile(fresh=True, probe_fstab=False)

        self.schema = None
        self.PartRecList = None
        self.pk2dict = {}   #maps PartitionRec.PKval to the associated schema dict


    def packPhysicalPartitions(self):
        ''' packs partitions together so that there are no gaps in partition
            numbers.
        '''
        # filter out non-partitions and spanning partitions
        physicalPartRecList = filter(lambda x: self.isPartition(x.PKval) and x['partition'] != '0', self.PartRecList)
        sortedPartRecList = sorted(physicalPartRecList, lambda x,y: int(x['partition'])-int(y['partition']))
        # partitions should have consecutive partition numbers. So check each
        # successive partition if it's greater than its predecessor by 1.
        # If not, then reassign the partition number.
        next_partition = 1
        for p in sortedPartRecList:
            if p['partition'] != str(next_partition):
                p['partition'] = str(next_partition)
            next_partition += 1
            if next_partition == 4:
                next_partition += 1

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
        self.packPhysicalPartitions()
        part_rules = self.PartRecList
        #reset the dictionary as we recreate it here.
        self.pk2dict.clear()
    
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
                    part_keys = disk['partition_dict'].keys()
                    part_keys = [ k for k in part_keys if not disk['partition_dict'][k].has_key('pv_span') ]
                    if not part_keys:
                        part_num = 1
                    else:
                        part_num = max(part_keys)+1
                    part_dict[part_num] = partition
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
        handleSpanPart = False
        try:
            disknum = int(partinfo['device'])
            #partinfo['partition'] contains lv name for lvs
            part_no = translatePartitionNumber(partinfo['partition'])
        except ValueError:
            if partinfo['device'].lower() == 'n':
                handleSpanPart = True
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
            raise InvalidPartitionSchema, "Partition number cannot be less than 1. %s" % partinfo['partition']
        partition = {'size_MB': size, 'fill': fill, 
                     'fs': fs, 'mountpoint': mountpoint,
                     'instid':partinfo.PKval, 'preserve': partinfo['preserve'] }
    
        if disk_dict.has_key(disknum): disk = disk_dict[disknum]
        else: disk = {'partition_dict': {}}
        disk['partition_dict'][part_no] = partition
        self.pk2dict[partinfo.PKval] = partition    #add the pk->dict mapping for the partition
        disk_dict[disknum] = disk
        if handleSpanPart:
            self.handleSpanningPartition(partinfo, disk_dict, vg_dict)

    def handleSpanningPartition(self, partinfo, disk_dict, vg_dict):
        '''Precondition:
            a. assume disk_dict already contains the PV info from partinfo
            b. assume that spanning PV's will always have device = 1, part_num = 'N'
        '''
        is_pv, vg_name = translatePartitionOptions(partinfo['options'], 'pv')
        if is_pv:
            vg_dict[vg_name]['pv_span'] = True
        else:
            if not 'pv' in [ x.lower() for x in partinfo['options'].split(';')]:
                raise NGEPartSchemaError , "non-PV partition marked as spanning multiple disks."

        #we're dealing with a PV:
        part_dict = disk_dict[1]['partition_dict']['N']
        assert(part_dict['instid'] == partinfo.PKval)
        part_dict['pv_span'] = True

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
        ''' adds a new PartitionRec object to the PartRecList - assumes it\'s not there yet '''
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

    def delPartRec(self,id):
        ''' removes partition record associated with an id 
        '''
        for i in xrange(len(self.PartRecList)):
            p = self.PartRecList[i]
            if p.PKval == id:
                del self.PartRecList[i]
                break
        
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

    def isVG(self,id):
        vg_list = getVGList(self.PartRecList, self.disk_profile)
        for p in vg_list:
            if p.PKval == id:
                return True
        return False

    def getPVMap(self):
        ''' returns a map of all PV PartRec ids mapping to an associated VG, if any
        '''

        part_list = getPartList(self.PartRecList, self.disk_profile)
        allPVmap = {}

        for p in part_list:
            ispv,vg = translatePartitionOptions(p['options'],'pv')
            if ispv:
                allPVmap[p.PKval] = vg
            else:
                #may still be an unassociated PV
                if 'pv' in [x.lower() for x in p['options'].split(';')]:
                    allPVmap[p.PKval] = None

        return allPVmap


    def getNewPartId(self):
        if not self.PartRecList:
            return -1
        minid = 0
        for p in self.PartRecList:
            if p.PKval < minid:
                minid = p.PKval
        return minid-1

    def createRowText(self, colTexts, colWidths, justification):
        return self.__createRowText(colTexts, colWidths, justification)

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
        self.static = False #do not invoke the plugin everytime	
        self.interactive = False #default to non-interactive
        self.__compname = None
        
    def isStatic(self):
        return self.static
        
    def isInteractive(self):
        return self.interactive

    def setComponentName(self, compname):
        self.__compname = compname

    def getComponentName(self):
        return self.__compname

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
        
    def update(self, currentNG):
        ''' Method for static plugins to run at every time 
        '''
        pass        

    def finished(self, currentNG, prevNG):
        ''' Method for Generic plugins to run at finish 
        '''
        pass

    def getPluginName(self):
        ''' Method to get the Generic Plugin Name 
        '''
        pass      

class NGPluginLibBase:
    """Interface to create a re-useable library that provides utility methods  
       to add or remove a component.
       
       The library can be used by interactive plug-ins that obtain user  
       input from either the TUI or from the node group XML configuration file. 
    """
    
    def __init__(self, database, kusuApp, **kwargs):
        self.database = database
        self.kusuApp = kusuApp
        self.ngid = None
        self.compName = None
        self.batchMode = False
        
    def getComponentID(self, compName):
        # Determine component ID
        query = '''select r.ostype from nodegroups ng, repos r where
                   ng.repoid = r.repoid and ng.ngid = %s''' %self.ngid
        self.database.execute(query)
        ostype, = self.database.fetchone()
        #we want to only pick up the components associated with the kits available in the
        #repo.We cant use ng_has_comp because we are building that very association here.
        #We work backwards by looking at the repository the nodegroup is backed by and
        #obtain the list of kits present within. 

        query = '''SELECT c.cid FROM components c ,  repos_have_kits  rk , nodegroups ng
        WHERE ( '%s' like textcat (os,'%%')  OR os IS NULL )
        AND cname = '%s'  AND c.kid = rk.kid
        AND ng.repoid = rk.repoid  AND ng.ngid = %s''' %(ostype,compName,self.ngid)

        self.database.execute(query)
        rv = self.database.fetchall()
        assert(len(rv)==1)  #exactly one component must match
        return int(rv[0][0])        

    def validate(self):
        '''Validates plug-in data before calling add()'''
        return True, 'Success'

    def add(self):
        '''Defines actions to execute when adding a component'''
        pass

    def remove(self):
        '''Defines actions to execute when removing a component'''
        pass
    
    def getNodeGroupID(self):
        return self.ngid
    
    def setNodeGroupID(self, ngid):
        self.ngid = ngid
    
    def getComponentName(self):
        return self.compName
    
    def setComponentName(self, compName):
        self.compName = compName
        
    def isBatchMode(self):
        return self.batchMode
    
    def setBatchMode(self, batchMode):
        self.batchMode = batchMode


class NGEScreenFactory(ScreenFactory):
    def __init__(self, screenlist):
        ScreenFactory.screens = screenlist


# Some utility functions

def getNGLockFile(ngid):
    return LockDir + "/%s.lock" % ngid
    
def isNGLockFileExists(ngid):
    lockFile = getNGLockFile(ngid)
    return os.path.exists(lockFile)

def createNGLockFile(ngid):
    if not os.path.exists(LockDir):
        os.mkdir(LockDir)
    
    lockFile = getNGLockFile(ngid)
    if not os.path.exists(lockFile):
        lock = path.path(lockFile)
        lock.touch()

def removeNGLockFile(ngid):
    lockFile = getNGLockFile(ngid)
    if os.path.exists(lockFile):
        lock = path.path(lockFile)
        lock.remove()

def getAvailPkgs(db, repoid, categorized=False):
    '''Returns a dictionary containing info for all of the packages 
       contained in the specified repository. Note: it takes time to 
       generate the package list.
       
       Params: if categorized is False, dictionary key is alphabetic letter
                     result[letter] => package name                  (faster)
               if categorized is True, dictionary key is category
                     result[category][group] => [package,package,...]         (slower)
       Returns: see previous
       Throws: NodeGroupError
    '''
    
    timediff = []
    result = {}

    if repoid is None:
        raise NodeGroupError, "Must specify a repository to get the list of available packages"

    from kusu.repoman import tools as rtool
    from kusu.core import database as sadb
    engine = os.getenv('KUSU_DB_ENGINE', 'postgres')
    dbinst = sadb.DB(engine, db='kusudb',username='nobody')

    repoObj = dbinst.Repos.get(repoid)
    os_name = repoObj.os.name
    repodir = repoObj.repository.strip()

    try:
        packdirs = rtool.getPackagePath(dbinst, repoid)
        if os_name.lower() not in ['sles', 'opensuse', 'suse']:
            compsfile = glob.glob(os.path.join(repodir, rtool.getBaseYumDir(dbinst, repoid), 'repodata','comps*.xml'))[0]

    except:
        raise NodeGroupError, "Cannot retrieve package info from selected " \
            "repository (ostype=%s) because it cannot be used at this time. " % os_name

    cwdbackup = os.getcwd()
    repopacklst = []
    repopackdirs = [str(x) for x in packdirs if x.exists()]
    for d in repopackdirs:
        # We want absolute pathnames here
        repopacklst += path.path(d).files('*.[rR][pP][mM]')

    repopacklst = [ path.path(RpmNameSplit(x)[0]).basename() for x in repopacklst if RpmNameSplit(x)[0] != '' ]
    repopackset = Set(repopacklst) #work with the set

    #remove packages coming from kits available through the current repo
    rmpacklst = []
    rmpackpathlist = []
    if db.driver == 'mysql':
       query = '''SELECT k.kid, k.rname FROM kits k, repos_have_kits rk,
       repos r WHERE r.repoid = rk.repoid AND rk.kid = k.kid AND
       k.isOS = False AND r.repoid = %s ''' %repoid
       db.execute(query)
    else: # postgres for now
       query = '''SELECT k.kid, k.rname FROM kits k, repos_have_kits rk,
       repos r WHERE r.repoid = rk.repoid AND rk.kid = k.kid AND
       k."isOS" = False AND r.repoid = %s ''' %repoid
       db.execute(query,postgres_replace=False)

    rv = db.fetchall()
    
    kits_root = db.getAppglobals('DEPOT_KITS_ROOT')
    for kitid, kitname in rv:
        kit_path = path.path(kits_root) / str(kitid)
        os.chdir(str(kit_path))
        kitpacklst = glob.glob('*.[rR][pP][mM]')
        
        if kitname.endswith('-updates'):
            kitpacklst = [x for x in kitpacklst if (x.startswith('component-') or x.startswith('kit-'))]
        
        rmpackpathlist.extend([str(kit_path / x) for x in kitpacklst])
        kitpacklst = [ RpmNameSplit(x)[0] for x in kitpacklst if RpmNameSplit(x)[0] != '' ]
        rmpacklst.extend(kitpacklst)
    
    #rmpacklst = [ x for x in rmpacklst if not x.startswith('kit-') ]
 
    repopackset -= Set(rmpacklst)
    os.chdir(cwdbackup)

    if not categorized: #alphabetic view

        curletter = None
        i = -1
        for p in sorted(repopackset):
            letter = p[0]
            if letter != curletter:
                result[letter] = []
                i += 1
                curletter = letter
            result[letter].append(p)

    elif not os_name.lower() in ['sles', 'opensuse', 'suse']: #category view
        
        import yum.comps
        from kusu.kitops.package import PackageFactory

        t1 = time.time()
        #instantiate comps
        compsinst = yum.comps.Comps()
        compsinst.add(compsfile)

        tmpcnt = 0
        ci = 0 #category index
        for c in compsinst.categories:
            result[c.name] = {}
            gi = 0
            for g in sorted(c.groups):
                ginst = compsinst.return_group(g)
                set2show = None
                if ginst: #some groups don't have any packages
                    set2show = repopackset & Set(ginst.packages)
                if set2show:  # do we have a non-empty intersection?
                    result[c.name][g] = []
                    for p in sorted(set2show):
                        tmpcnt+=1
                        result[c.name][g].append(p)
                    #done package
                    repopackset -= set2show
                    gi += 1
            #done group
            ci += 1
        #done category

        t2 = time.time()
    
        #construct group dictionary for remaining packages
        result["Other"] = {}
        groupdict = result["Other"]
         
        tmpcnt2 = 0
        for p in repopackset:
            #reconstruct the full package name to pass to PackageFactory
            for d in repopackdirs:
                tmplst = glob.glob("%s/%s-[0-9]*" % (d, p))
                if not tmplst: #corner case
                    tmplst = glob.glob("%s/%s-*.rpm" % (d, p))
                pfile = tmplst[0]
                #get group through my package library -> RPMTAG_GROUP
                pinst = PackageFactory(pfile)
                group = pinst.getGroup()
                if group not in groupdict.keys():
                    groupdict[group] = [] #initialize
                tmpcnt2 += 1
                groupdict[group].append(p)
               
        t3 = time.time()

        kl.debug("Optional Packages: comps: %d, unlisted: %d;\ntcomps=%f;\t" %(tmpcnt, tmpcnt2,t2-t1) +\
            "time to build d.s. for other=%f" %(t3-t2,))

    else: # Categorized view for sles
        from primitive.support.rpmtool import RPM, RPMCollection
        from kusu.kitops.package import PackageFactory

        t1 = time.time()
        #build list of packages
        cwdbackup = os.getcwd()
        repopathlist = []
        for d in repopackdirs:
            os.chdir(d)
            repopathlist.extend([os.path.join(d, x) for x in glob.glob('*.[rR][pP][mM]')])

        kitpacks = RPMCollection()
        for rpm_file in rmpackpathlist:
            kitpacks.add(RPM(rpm_file))

        os.chdir(cwdbackup)
        repopacklist = [RPM(x) for x in repopathlist]
        repopackset = RPMCollection()
        for rpm in repopacklist:
            if not kitpacks.RPMExists(rpm.getName(), rpm.getArch()):
                repopackset.add(rpm)
        
        for pack in repopackset.getList():
            pack_name = pack.getName()
            hdr = pack.getGroup()
            if hdr and hdr != '':
                try:
                    cat, grp = hdr.split('/',1)
                except ValueError:
                    if hdr not in result:
                        result[hdr] = []
                    result[hdr].append(pack_name)
                
                if cat not in result:
                    result[cat] = {}
                if grp not in result[cat]:
                    result[cat][grp] = []
                result[cat][grp].append(pack_name)
            
            else:
                if 'others' not in result:
                    result['others'] = []
                result['others'].append(pack_name)
        
    return result


def getAvailModules(db, ngid, repoid=None, comps=None):
    '''Returns a dictionary containing info for all of the modules 
       included in the driver packs for a specified list of components.
       Note: it takes time to generate the modules list.
       
       Params: comps = list of component IDs
       Returns: result[letter] => [{'name':module,'desc':desc}, 
                                   {'name':module,'desc':desc}, ...]
       Throws: NodeGroupError
    '''    
    
    result = {}
    
    if not ngid:
        raise NodeGroupError, "Must specify a node group to retrieve the module list."

    if ngid == db.getNgidOf('unmanaged'):
       raise NodeGroupError, "Unmanaged nodegroup is not supported."

    #get repository information

    if repoid is None:
        query = "select r.repoid, r.repository, r.ostype from repos r, nodegroups n " \
                "where r.repoid = n.repoid and n.ngid = %s" % ngid
        db.execute(query)
        repoid, repodir, ostype  = db.fetchone()
    else:
        query = "select r.repository, r.ostype from repos r where r.repoid = %s" % repoid
        db.execute(query)
        repodir, ostype  = db.fetchone()

    repodir = repodir.strip()

    from kusu.repoman import tools as rtool
    from kusu.core import database as sadb
    engine = os.getenv('KUSU_DB_ENGINE', 'postgres')
    dbinst = sadb.DB(engine, db='kusudb',username='nobody')

    try:
        packdirs = rtool.getPackagePath(dbinst, repoid)
    except KeyError:
        raise NodeGroupError, "Repository with ostype = %s is not supported." % ostype
    repopackdirs = [str(x) for x in packdirs if x.exists()]

    #2. obtain the name of driverpacks to examine
    if not comps:
        query = "select d.dpname from driverpacks d, ng_has_comp n where " \
                "d.cid = n.cid and n.ngid = %s" % ngid
    else:
        comps_lst = [str(comp) for comp in comps]
        comps_str = ','.join(comps_lst)
        query = "select d.dpname from driverpacks d where d.cid in (%s)" % comps_str
   
    db.execute(query)
    rv = db.fetchall()
    dpacklst = [x[0] for x in rv]
    # create a temp dir for ko files
    tmprootdir = mkdtemp()

    tmpdir = "%s" % tmprootdir + '/modules'
    if not os.path.exists(tmpdir):
         os.mkdir(tmpdir)

    tmpdir = "%s" % tmpdir + "/%s" % ngid 
    if not os.path.exists(tmpdir):
         os.mkdir(tmpdir)

    t1 = time.time()

    for dpack in dpacklst:
        dpackfull = ""
        for repopackdir in repopackdirs:
            dpackfull = "%s/%s" %(repopackdir,dpack)
            if os.path.exists(dpackfull):
                break
        
        if not os.path.exists(dpackfull):
            kl.warn('Driver package %s not found in repo %s'\
                                    %(dpack,repodir))
        else:
            #3. extract the driverpack's ko files (can't use rpmtool.extract)
            cmd = "rpm2cpio %s | cpio -id *.ko" %dpackfull
            p = subprocess.Popen(   cmd, shell=True, 
                                    cwd = tmpdir,
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.PIPE
                                 )
            p.communicate()

    t2 = time.time()

    #4. populate the module dictionary with description
    moddict = {}    #dictionary of modules & their description
    cmd = 'find %s -name "*.ko" | xargs modinfo | egrep "^filename|^description"'  %tmpdir
    p = subprocess.Popen(cmd, shell=True, cwd = tmpdir,
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.PIPE
                         )
    rv = p.communicate()[0]
    fname = None
    for line in rv.split('\n'):
        if line.startswith('filename:'):
            fname = line.split(':',1)[1].strip() #path/file.ext
            fname = os.path.splitext(os.path.split(fname)[1])[0]
            moddict[fname] = ''
        elif line.startswith('description:'):
            if not moddict[fname]: #only one description - posible >1 desc field per module
                moddict[fname] = line.split(':',1)[1].strip()

    t3 = time.time()
    shutil.rmtree(tmprootdir)
    kl.debug("Modules screen: \ndriver rpm extraction: %f\ndesc info extraction: %f\nmoddict len = %d" \
                %(t2-t1,t3-t2, len(moddict))
            )

    curletter = None
    i = -1
    for m in sorted(moddict):
        letter = m[0]
        if letter != curletter:
            result[letter] = []
            i += 1
            curletter = letter
        result[letter].append({'name':m,'desc':moddict[m]})
             
    return result


def delScripts(db, scripts=[]):
    '''Delete scripts from the script repo only if it's currently 
     not used by any node groups'''
 
    destDir = db.getAppglobals('DEPOT_REPOS_SCRIPTS')
    if not destDir: destDir = '/depot/repos/custom_scripts'
    for script in scripts:
        scriptPath = os.path.join(destDir,script)
        if os.path.isfile(scriptPath):
            db.execute("select script from scripts where script='%s'" %script)
            rv = db.fetchall()
            if not rv:
                # No node groups are using this script, remove it
                os.remove(scriptPath)

def copyScripts(db, scriptPaths=[]):
    '''Copy list of scripts to script repo and return to the caller 
       a list of scripts that were copied
       
       Throws: NGEValidationError if problem was found. All copied 
       scripts will be removed before returning. 
    '''

    destDir = db.getAppglobals('DEPOT_REPOS_SCRIPTS')
    if not destDir: destDir = '/depot/repos/custom_scripts'
    errMsg = None
    copiedScripts = []

    for srcPath in scriptPaths:
        head,tail = os.path.split(srcPath)
        if not head:
            #no path given - assume user specified an existing script
            if not os.path.isfile(os.path.join(destDir,tail)):
                errMsg = "Specified script '%s' doesn't exist in the script repository" % tail
                break
        else:
            #full path given
            if not os.path.isabs(srcPath):
                errMsg = "Script path '%s' must be an absolute path" % srcPath
                break
            if not os.path.isfile(srcPath):
                errMsg = "Script path '%s' does not refer to a valid file" % srcPath
                break

            if os.path.realpath(os.path.normpath(srcPath)) != \
               os.path.normpath(os.path.join(destDir,tail)):
            
               #dealing with an existing file outside script repo
               #ensure name uniqueness
               db.execute("select script from scripts where script='%s'" %tail)
               rv = db.fetchall()
               if len(rv) >=1 or tail in os.listdir(destDir):
                   errMsg = "Script name '%s' conflicts with an existing script name" % tail
                   break
               else:
                   shutil.copy(srcPath,destDir)
                   copiedScripts.append(tail)

    # cleanup on failure
    if errMsg:
        delScripts(db, copiedScripts)
        raise NGEValidationError,errMsg

    return copiedScripts
