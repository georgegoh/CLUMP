#!/usr/bin/env python
# $Id: settings.py 3517 2010-02-12 09:19:08Z kunalc $
#
# Copyright 2009 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
import re
from kusu.util.errors import InvalidMetaXMLError, UnknownSettingNameError, SettingNotFoundError, InvalidAppglobalValueError
from kusu.core import database as sadb
from kusu.appglobals.metadata import Metadata
from sqlalchemy.exceptions import InvalidRequestError


class Settings:
    def __init__(self, meta_files=[]):
        engine = os.getenv('KUSU_DB_ENGINE', 'postgres')
        self.dbs = sadb.DB(driver=engine, db='kusudb', username='apache')
        self.metadata = Metadata(meta_files).metadata

    def getAppglobal(self, name):
        try:
            setting_metadata = self.metadata[name]
        except KeyError:
            raise UnknownSettingNameError, "Setting '%s' was not recognized from the metadata" % name

        try:
            kname = setting_metadata['kname']
        except KeyError:
            raise InvalidMetaXMLError, "Missing required 'kname' element in Appglobal metadata setting '%s'" % name

        try:
            return self.dbs.AppGlobals.selectone_by(kname=kname).kvalue
        except InvalidRequestError:
            raise SettingNotFoundError, "Setting '%s' not present in PCM database" % name

    def isValidAppglobal(self, value, setting_metadata):
        try:
            allowed_type, allowed = setting_metadata['allows']
        except KeyError:
            raise InvalidMetaXMLError, "Missing required 'allows' element in Appglobal metadata"

        if allowed_type == 'list':
            allowed = [x[1] for x in allowed]
            return value in allowed

        elif allowed_type == 'regex':
            return re.search(allowed, value) is not None

        elif allowed_type == 'explanation':
            return True

        else:
            raise InvalidMetaXMLError, "Appglobal metadata contains unrecognized allowed_type: '%s'" % allowed_type

    def setAppglobal(self, name, value):
        value=str(value)

        try:
            kname = self.metadata[name]['kname']
        except KeyError:
            raise UnknownSettingNameError, "Setting '%s' was not recognized from the metadata" % name

        if not self.isValidAppglobal(value, self.metadata[name]):
            raise InvalidAppglobalValueError, "Value '%s', is invalid for Appglobal setting '%s'" % (value, name)

        try:
            setting = self.dbs.AppGlobals.selectone_by(kname=kname)
            setting.kvalue = value
        except InvalidRequestError:
            setting = self.dbs.AppGlobals(kname=kname, kvalue=value)

        setting.save()
        self.dbs.flush()

    def displayAppglobalValue(self, name):
        try:
            value = self.getAppglobal(name)
        except (InvalidMetaXMLError, UnknownSettingNameError), e:
            print "Error: %s" % str(e)
        except SettingNotFoundError, e:
            print "%-30s: Setting was not found in the PCM database" % name
        else:
            print '%-30s: %-30s' % (name, value)

    def displayAllAppglobalValues(self):
        for name in self.metadata:
            self.displayAppglobalValue(name)

