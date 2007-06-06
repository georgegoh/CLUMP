#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

import kusu.util.log as kusulog

kl = kusulog.getKusuLog('util.profile')

class Profile(dict):
    """
    The Kusu installer profile, inherits from built-in type dict.

    This class stores configuration information by context. The information can
    be stored in any form. The profile object will write configuration
    information to a database according to functions specified by the 
    configuration information generating entities.
    """

    save_functions = []
    database = None

    def __init__(self, d={}):
        """
        Use d as the dictionary.
        """

        dict.__init__(self, d)

    def restore(self):
        """
        Restore profiles from DB by calling each provided restore function.
        """

        for func, profile in self.save_functions:
            self.runFunc(func[0], profile)

    def save(self):
        """
        Save all profiles to DB by calling each provided save function.
        """

        for func, profile in self.save_functions:
            self.runFunc(func, profile)

    def runFunc(self, func, profile):
        """
        Run DB operation function.
        """

        if func is None:
            kl.debug('Attempted to execute None function')
            return

        rv = func(self.database, profile, self.copy())
        if rv:
            kl.debug("SUCCESS executing %s with profile '%s'" %
                     (func.__str__(), profile))
        else:
            kl.debug("FAIL executing %s with profile '%s'" %
                     (func.__str__(), profile))

    def addDatabase(self, db):
        """
        Provide database connection.
        """

        self.database = db

    def getDatabase(self):
        """
        Returns the database currently used. Take care not to close this object.
        """

        return self.database

    def addFunctions(self, func, profile):
        """
        Add function to be called when saving profile to DB.

        Arguments:
        func -- the function to call. Function signature should be:
                func(db, profile_str, profile_dict)
                where db is the database to write to,
                      profile_str is the string representation of the profile
                      profile_dict is the actual data for this profile
        profile -- string indicating the profile to pass to the function
        """

        if (func, profile) not in self.save_functions:
            self.save_functions.append((func, profile))
            kl.debug("Appended %s with profile '%s'" %
                     (func.__str__(), profile))

        try:
            self[profile]
        except KeyError:
            self[profile] = {}

class PersistantProfile:
    def __init__(self, kiprofile):
        kiprofile.addFunctions(self.save, self.profile)

        self.restore(kiprofile.getDatabase(), self.profile, kiprofile)

    def save(self, db, profile, kiprofile):
        pass

    def restore(self, db, profile, kiprofile):
        pass

