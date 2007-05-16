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

    def save(self):
        """
        Save all profiles to DB by calling each provided save function.
        """

        for func, profile in self.save_functions:
            rv = func(self.database, profile, self[profile])
            if rv:
                kl.debug("SUCCESS executing %s with profile '%s'" %
                         (func.__str__(), profile))
            else:
                kl.debug("FAIL executing %s with profile '%s'" %
                         (func.__str__(), profile))

        kl.info('Committing database')
        self.database.commit()

    def addDatabase(self, db):
        """
        Provide database connection.
        """

        self.database = db

    def addSaveFunction(self, func, profile):
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
