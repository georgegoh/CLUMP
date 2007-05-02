#! /usr/bin/env python
#
#  $Id: kusudb.py 279 2007-04-12 19:53:16Z atumanov $
#
#  Copyright 2007 Platform Computing Corporation
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


from MySQLdb import *
#commenting this out for now as it's only avail. on my dev. box
#from Crypto.Cipher import Blowfish
import sys

class KusuDB:
    """KusuDB class will handle Kusu DB connections, own the connection handle,
       process queries, manage transactions, and otherwise implement database
       related functionality"""

    def __init__(self):
        self.dbname	= 'kusudb'
        self.dbuser	= 'nobody'
        self.dbpasswd	= ''
        self.__passfile	= '/opt/kusu/etc/db.passwd'

        self.__dbconn	= None
        self.__dbcursor	= None

    def __del__(self):
        self.disconnect()

    def connect(self, dbname=None, user=None, passwd=None):
        if dbname:
            self.dbname = dbname
        if user:
            self.dbuser = user
        if passwd:
            self.dbpasswd = passwd

        tmppass = ''
        #fetch apache's passwd
        if self.dbuser == 'apache':
            tmppass = self.__getPasswd()
        
        if not tmppass: #could be either None or ''
            tmppass = self.dbpasswd
        try:
            # print "KusuDB: connecting as %s:%s@%s" % (self.dbuser, tmppass, self.dbname)
            self.__dbconn = connect(user='%s' %self.dbuser, passwd='%s' %tmppass, \
                                    db='%s' %self.dbname)
        except OperationalError,msg:
            print "KusuDB: Operational Error occurred when connecting to the DB\n"+\
                  "       Most likely cause: insufficient permissions for user=%s" %self.dbuser
            print msg
            raise OperationalError,msg
        else:
            #no exception occurred - obtain cursor
            self.__dbcursor = self.__dbconn.cursor()
            self.__dbconn.autocommit(True)

        tmppass = ''
            
    def disconnect(self):
        if not self.isconnected():
            return
        self.__dbcursor.close()
        self.__dbconn.close()
        self.__dbconn = self.__dbcursor = None

    def execute(self, query):
        if not self.isconnected():
            print "KusuDB: Connect to the Database first using connect([db,[user,[pass]]])"
            return None
        return self.__dbcursor.execute(query)

    def fetchone(self):
        if not self.isconnected():
            print "KusuDB: Connect to the Database first using connect([db,[user,[pass]]])"
            return None
        return self.__dbcursor.fetchone()

    def fetchall(self):
        if not self.isconnected():
            print "KusuDB: Connect to the Database first using connect([db,[user,[pass]]])"
            return None
        return self.__dbcursor.fetchall()

    def __getPasswd(self):

        #try opening self.__passfile - catch an exception if it fails
        try:
            fp = file(self.__passfile, 'r')
        except IOError,msg:
            print "KusuDB: insufficient priviledges to access password file for DB user %s" %self.dbuser
            print "       optionally, the password file may be missing"
            print msg
            return None
        except:
            print "KusuDB: error accessing the password file for user %s" %self.dbuser
            return None

        cipher = fp.readline().strip()
        fp.close()
        return self.__decrypt(cipher)

    def  __decrypt(self, cipher):
        #convert cipher to decrypted text
        return cipher

    def __encrypt(self):
        pass

    def isconnected(self):
        if self.__dbconn == None:
            return False
        else:
            return True

    def beginTransaction(self):
        """ Returns True if transaction was successfully started and False otherwise"""

        try:
            self.execute('START TRANSACTION')
        except OperationalError,msg:
            print "KusuDB: DB user used did not have proper permissions to start transaction" 
            print msg
        except Exception,msg:
            print "KusuDB: general exception occurred while starting transaction\n"
            print msg
        else:
            #no exceptions occurred
            return True

        return False

    def endTransaction(self):
        return self.__commit()

    def undoTransaction(self):
        return self.__rollback()

    def __commit(self):
        if not self.isconnected():
            print "KusuDB: Connect to the Database first using connect([db,[user,[pass]]])"
            return None
        return self.__dbconn.commit()

    def __rollback(self):
        if not self.isconnected():
            print "KusuDB: Connect to the Database first using connect([db,[user,[pass]]])"
            return None
        return self.__dbconn.rollback()

    def getAppglobals(self, kname):
        """getAppglobals - This method will query the appglobals table for
        a specified kname, and return the kvalue.  No exceptions will be
        thrown, instead an empty string will be returned."""
        query = ('select kvalue from appglobals where kname="%s"' % kname)
        try:
            self.execute(query)
        except:
            return ''
        data = self.fetchone()
        if data:
            return data[0]
        return ''

    def getDescription(self):
        if not self.isconnected():
            print "KusuDB: Connect to the Database first using connect([db,[user,[pass]]])"
            return None
        return self.__dbcursor.description

    def printDebugInfo(self):
        if self.isconnected():
            print "KusuDB: Server capabilities: 0x%x" % self.__dbconn.server_capabilities
            print "KusuDB: capabilities & transactional_flag = 0x%x" % self.__dbconn._transactional
            print 'KusuDB: DB connection info: %s' % self.__dbconn.get_host_info()
        else:
            print "KusuDB: Connect to the Database first using connect([db,[user,[pass]]])"
        

def printKusudbInfo():
    print 'DB-API Level = %s' %apilevel
    print 'DB-API Thread Safety = %d' %threadsafety
    print 'DB-API Parameter Formatting: %s' %paramstyle
    print 'MySQL client version = %s' %get_client_info()

if __name__ == "__main__":
    printKusudbInfo()
    mydb = KusuDB()
    mydb.connect('kusudb','apache')
    #mydb.connect()
    mydb.printDebugInfo()

    try:
        mydb.execute("select * from appglobals")
        #mydb.execute("insert into appglobals (kname,kvalue) values ('AlexTest','BirchTree')")
    except OperationalError,msg:
        print "MAIN: DB user used did not have proper permissions to execute the query" 
        print msg
        sys.exit(1)
    except Exception,msg:
        print "MAIN: general exception occurred executing the query\n"
        print msg
        sys.exit(1)

    #insert rollback test
    print "MAIN: insert rollback test"
    mydb.beginTransaction()
    mydb.execute("insert into appglobals (kname,kvalue) values ('AlexTest','PineTree')")
    mydb.undoTransaction()
    mydb.execute("select * from appglobals where kname='alextest'")
    junk = mydb.fetchall()
    for f1,f2,f3,f4 in junk:
        print "|%5s|%20s|%60s|%10s| " %(f1,f2,f3,f4)

    #insert commit test
    print "MAIN: insert commit test"
    mydb.beginTransaction()
    mydb.execute("insert into appglobals (kname,kvalue) values ('AlexTest','PineTree')")
    mydb.endTransaction()
    mydb.execute("select * from appglobals where kname='alextest'")
    #print mydb.getDescription()
    junk = mydb.fetchall()
    for f1,f2,f3,f4 in junk:
        print "|%5s|%20s|%60s|%10s| " %(f1,f2,f3,f4)

    #delete rollback test
    print "MAIN: delete rollback test"
    mydb.beginTransaction()
    mydb.execute("delete from appglobals where kname='alextest'")
    mydb.undoTransaction()
    mydb.execute("select * from appglobals where kname='alextest'")
    junk = mydb.fetchall()
    for f1,f2,f3,f4 in junk:
        print "|%5s|%20s|%60s|%10s| " %(f1,f2,f3,f4)

    #delete commit test
    print "MAIN: delete commit test"
    mydb.beginTransaction()
    mydb.execute("delete from appglobals where kname='alextest'")
    mydb.endTransaction()
    mydb.execute("select * from appglobals where kname='alextest'")
    junk = mydb.fetchall()
    for f1,f2,f3,f4 in junk:
        print "|%5s|%20s|%60s|%10s| " %(f1,f2,f3,f4)

    mydb.disconnect()
    if mydb.isconnected():
        print "MAIN: DB is connected but shouldn't be"
    else:
        print "MAIN: DB is not connected - expected behavior"
