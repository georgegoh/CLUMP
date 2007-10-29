import os
import string
import glob
import snack
from kusu.ngedit.ngedit import NGEPluginBase
from kusu.ui.text import USXkusuwidgets as kusuwidgets

class NGPlugin(NGEPluginBase):
    name= 'LSF Kit'
    msg = 'The screen sequence will display the License and prompt for the cluster name'

    def __init__(self, database, kusuApp=None, gridWidth=45):
        #important to keep this as lightweight as possible
        NGEPluginBase.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.setHelpLine("LSF plugin - please read carefully")
        self.interactive = True
        self.__basedocdir = "/depot/www/kits"
        self.__docdir = None
        self.__accepted = True
        self.__cid = None

    def drawImpl(self):

        compname = self.getComponentName()
        if not self.__cid:
            #determine the component ID
            query = '''select r.ostype from nodegroups ng, repos r where 
                       ng.repoid = r.repoid and ng.ngid = %s''' %self.ngid
            self.database.execute(query)
            ostype, = self.database.fetchone()

            query = '''select cid from components where ('%s' like concat(os,'%%')
                       or isnull(os))  and cname = '%s' ''' %(ostype, compname)
            self.database.execute(query)
            rv = self.database.fetchall()
            assert(len(rv)==1)  #exactly one component must match
            self.__cid = int(rv[0][0])

        if not self.__docdir:
            #get kitname, kitver for this component
            query = '''select k.rname, k.version from kits k, components c where 
                       c.cid = %s and c.kid = k.kid ''' %self.__cid
                       #c.cname='%s' and c.kid = k.kid ''' %compname
            self.database.execute(query)
            kitname,kitver = self.database.fetchone()
            self.__docdir = os.path.join(self.__basedocdir, kitname, kitver)

        license_file = os.path.join(self.__docdir, 'LICENSE')
        assert(os.path.isfile(license_file))    #FIXME: handle absense of license file

        fp = file(license_file, 'r')
        license_text = string.join(fp.readlines(),'')
        fp.close()

        msgbox = self.selector.popupDialogBox('Platform(TM) LSF(R) License Agreement',
                    'Please read carefully the following license agreement.\n' + \
                    license_text, ['Accept', 'Decline'])

        self.screenGrid = snack.Grid(1, 1)

        if msgbox.lower() == 'accept':
            #check whether it was previously declined
            if not self.__accepted:
                #restore the component association
                query = '''insert into ng_has_comp SET ngid=%s, cid=%s''' %(self.ngid, self.__cid)
                try:
                    self.database.execute(query)
                except:
                    pass
                self.__accepted = True

            self.cluname = kusuwidgets.LabelledEntry(labelTxt="Cluster Name: ", \
                                    width=30, password=0, returnExit = 0)
            self.screenGrid.setField(self.cluname, 0,0, (0,0,0,0))
            return

        #disassociate the component otherwise
        self.__accepted = False
        msg = "License agreement declined. This component will not be available "+\
              "for this nodegroup. Please continue."
        query = ''' delete from ng_has_comp where ngid=%s and cid=%s ''' %(self.ngid, self.__cid)
        self.database.execute(query)
        self.screenGrid.setField(snack.TextboxReflowed(text=msg,
                                 width=self.gridWidth), 0,0, (0,0,0,0) )

    def validate(self):
        if self.__accepted:
            cluname = self.cluname.value().strip()
            if not cluname:
                return False, "Empty string is not a valid cluster name."
        return True, "Success"

    def add(self):
        if not self.__accepted:
            #nothing to do
            return
        cluname = self.cluname.value().strip()

        query = "select * from appglobals where ngid=%s and kname='LSFClusterName'" %self.ngid
        self.database.execute(query)
        rv = self.database.fetchone()
        if rv:
            #this global already exists - update it
            query = '''update appglobals set kvalue='%s' where kname='LSFClusterName' 
                       and ngid=%s ''' %(cluname, self.ngid)
        else:
            query = '''insert into appglobals (kname,kvalue,ngid) values 
                       ('LSFClusterName', '%s', %s) ''' %(cluname,self.ngid)
        self.database.execute(query)

    def remove(self):
        #anything to do here?
        pass
