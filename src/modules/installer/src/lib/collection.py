#!/usr/bin/env python
# $Id$
#
# Kusu Installer Data Container Module
#
# Kusu Text Installer Framework.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
"""This module is the data container - any user can deposit context-based key/value
   pairs into the objects here."""

import pickle
class SettingsContainer:
    """A collection of settings for a particular context."""
    context = ''
    settings = {}

    def __init__(self, context):
        self.context = context


class PickledSettingsCollection:
    """A collection of containers, stored in a flat file."""
    contexts = {}

    def __init__(self, database='collection.pic'):
        self.database = database
        self.checkout(database)

    def put(self, context, key, value):
        """Put in a context-based key/value pair."""
        if self.contexts.has_key(context):
            container = self.contexts[context]
        else:
            container = SettingsContainer(context)
            self.contexts[context] = container
        container.settings[key] = value

    def getContexts(self):
        """Get all contexts stored previously."""
        return self.contexts.keys()

    def get(self, context, key):
        """Get the value associated with a given context and key."""
        if not self.contexts.has_key(context):
            return None
        container = self.contexts[context]
        if not container.settings.has_key(key):
            return None
        return container.settings[key]

    def commit(self):
        """Save all transactions."""
        f = file(self.database, 'wb')
        pickle.dump(self, f, -1)
        f.close()

    def checkout(self, src):
        """Load database into memory from a given source file."""
        if not self.__isFileExists(src):
            return
        f = file(src, 'rb')
        cp = pickle.load(f)
        self.name = cp.name
        self.contexts = cp.contexts
        f.close()

    def __isFileExists(self, filename):
        """Private function - Checks if file with given filename exists."""
        try:
            f = open(filename)
            f.close()
        except IOError, e:
            if e.errno == 2:
                return False
        return True

from pysqlite2 import dbapi2 as sqlite
class SQLiteCollection:
    """A Collection implemented with SQLite."""
    table_name = 'installer_settings'
    id_col = 'id'
    context_col = 'context'
    setting_col = 'setting'
    value_col = 'value'

    def __init__(self, database='kusu.db'):
        self.checkout(database)

    def put(self, context, key, value):
        """Put in a context-based key/value pair."""
        self.remove(context, key)
        statement = 'INSERT INTO ' + self.table_name + \
                    ' ('+self.context_col+', '+self.setting_col+', '+self.value_col+') ' + \
                    'VALUES ("'+context+'", "'+key+'", "'+value+'")'
        self.cur.execute(statement)

    def getContexts(self):
        """Get all contexts stored previously."""
        all_rows = self.get()
        contexts = []
        for row in all_rows:
            if row[1] not in contexts:
                contexts.append(row[1])
        return contexts

    def get(self, context='*', key='*'):
        """Get a value, or a set of values that correspond to the context and
           key provided.

           get(self, context='*', key='*')

           If context _and_ key are both provided, this function returns a list
           of only value(s) that correspond to both the context and the key.

           Else if only one of the parameters is provided, then this
           function will return a list of tuples that match that parameter
           in the format (id, context, setting, value).

           Else no parameters provided, this function will return all rows in
           the database in a list of tuples in the format (id, context, setting,
           value).
        """
        column_returned = self.value_col
        if(context == '*' or key == '*'):
            column_returned = '*'
        statement = 'SELECT ' + column_returned + ' FROM ' + self.table_name
        if(context != '*' or key != '*'):
            added_criteria = ' WHERE '
            if(context != '*'):
                added_criteria = added_criteria+self.context_col+' == "'+context+'"'
            if(context != '*' and key != '*'):
                added_criteria = added_criteria+' AND '
            if(key != '*'):
                added_criteria = added_criteria+self.setting_col+' == "'+key+'"'
            statement = statement + added_criteria
        self.cur.execute(statement)
        retVal = []
        for row in self.cur:
            if(context == '*' or key == '*'):
                retVal.append(row)
            else:
                retVal.append(row[0])
        return retVal

    def remove(self, context, key):
        """Remove from the database the value associated with the given
        context and key.
        """
        statement = 'DELETE FROM ' + self.table_name + ' WHERE ' + \
                    self.context_col + ' == "' + context + '" AND ' + \
                    self.setting_col + ' == "' + key + '"'
        self.cur.execute(statement)

    def commit(self):
        """Save all transactions."""
        self.con.commit()

    def checkout(self, src):
        """Load database into memory from a given source file."""
        if self.__isFileExists(src) is False:
            self.__createNewDB(src)
        self.con = sqlite.connect(src)
        self.cur = self.con.cursor()

    def __isFileExists(self, filename):
        """Private function - Checks if file with given filename exists."""
        try:
            f = open(filename)
            f.close()
        except IOError, e:
            if e.errno == 2:
                return False
        return True

    def __createNewDB(self, filename):
        """Private function - Create a new DB."""
        f = open(filename, 'w')
        f.close()
        con = sqlite.connect(filename)
        cur = con.cursor()
        statement = 'CREATE TABLE installer_settings (' + \
                    'id INTEGER PRIMARY KEY AUTOINCREMENT, ' + \
                    'context TEXT, ' + \
                    'setting TEXT, ' + \
                    'value TEXT)'
        cur.execute(statement)
        con.commit()
        con.close()

    def close(self):
        """Saves all transactions and closes the DB connection."""
        self.con.commit()
        self.con.close()

import os
import unittest
class SQLiteCollectionTestCase(unittest.TestCase):
    def setUp(self):
        tmpfile = '/tmp/collection.db'
        try:
            os.remove(tmpfile)
        except OSError, e:
            assert e.errno == 2, "OSError exception thrown"
        self.collection = SQLiteCollection(tmpfile)

    def tearDown(self):
        print 'Test case done. Closing connection.'
        self.collection.close()
        self.collection = None

    def testPutAndGet(self):
        """Do the standard action expected of users."""
        print 'Testing collection.put'
        self.collection.put('context1', 'setting1', 'value1')
        listtuple_result = self.collection.get()
        assert listtuple_result[0] == (1, 'context1', 'setting1', 'value1'), \
                                      "Didn't get the same tuple as I put in."
        print 'Got the same tuple I put in.'
        list_result = self.collection.get('context1', 'setting1')
        assert list_result[0] == 'value1', "Didn't get the right value from" + \
                                 " context/setting pair."
        print 'Got the same value I put in.'

    def testMultiplePutAndGet(self):
        """Put in multiple different values into the same context and setting. \
           Should reflect only the last value put in."""
        print 'Testing collection multiple put.'
        self.collection.put('context1', 'setting1', 'value1')
        self.collection.put('context1', 'setting1', 'value2')
        self.collection.put('context1', 'setting1', 'value3')
        self.collection.put('context1', 'setting1', 'value4')
        listtuple_result = self.collection.get()
        print listtuple_result
        assert listtuple_result[0] == (4, 'context1', 'setting1', 'value4'), \
                                      "Didn't get the same tuple as I last put in."
        print 'Got the same tuple I last put in.'
        list_result = self.collection.get('context1', 'setting1')
        assert list_result == ['value4'], "Didn't get the right value from" + \
                                 " context/setting pair I last put in."
        print 'Got the same value I last put in.'

    def testRemove(self):
        """Test the remove functionality."""
        print 'Testing collection remove.'
        self.collection.put('context1', 'setting1', 'value1')
        self.collection.remove('context1', 'setting1')
        listtuple_result = self.collection.get()
        assert listtuple_result == [], 'Currypot not empty after call to remove.'
        print 'Successful remove.'

    def testMultipleContexts(self):
        """Create 2 contexts with same key/value pairs, and ensure that only
           key/value pairs of the requested context are returned."""
        print 'Testing multiple contexts.'
        self.collection.put('context1', 'setting1', 'wrong')
        self.collection.put('context2', 'setting1', 'right')
        self.collection.put('context1', 'setting2', 'wrong')
        self.collection.put('context2', 'setting2', 'right')
        self.collection.put('context1', 'setting3', 'wrong')
        self.collection.put('context2', 'setting3', 'right')
        self.collection.put('context1', 'setting4', 'wrong')
        self.collection.put('context2', 'setting4', 'right')

        listtuple_result = self.collection.get('context2')
        for tup in listtuple_result:
            assert tup[3] == 'right', "Didn't get the right value from " + \
                             "context-sensitive get."
            print tup, 'OK'

        list_result = self.collection.get('context1', 'setting3')
        assert list_result == ['wrong'], "Didn't get the same value as I put in"
        print "Got the same value as I put in."

if __name__ == "__main__":
    suite = unittest.makeSuite(SQLiteCurrypotTestCase, 'test')
    runner = unittest.TextTestRunner()
    runner.run(suite)
