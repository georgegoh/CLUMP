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
            rv = func(self.database)
            
            if isinstance(self[profile], dict) and isinstance(rv, dict):
                self[profile].update(rv)
            else:
                self[profile] = rv

    def save(self):
        """
        Save all profiles to DB by calling each provided save function.
        """

        for func, profile in self.save_functions:
            func(self.database, self[profile])

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
            kl.debug("Appended function %s with profile '%s'" %
                     (func.__str__(), profile))

        try:
            self[profile]
        except KeyError:
            self[profile] = {}

class PersistentProfile:
    def __init__(self, kiprofile):
        kiprofile.addFunctions(self.save, self.profile)

        self.restore(kiprofile.getDatabase())

    def save(self, db, profile):
        """
        Store profile to database.

        Arguments:
        database -- the database to which to store the profile
        profile -- the profile belonging to this object
        """
        pass

    def restore(self, db):
        """
        Restore profile from db.

        This function will read the database specified by db and return the
        profile belonging to this object.
        """
        pass

