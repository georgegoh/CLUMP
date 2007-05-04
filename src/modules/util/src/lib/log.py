#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

__version__ = "$Rev:$"

import os
import logging
from logging.handlers import SysLogHandler, SYSLOG_UDP_PORT
from path import path

#def getLogger(name='kusulog'):
def getLogger(name='kusulog'):
    return logging.getLogger(name)

def getKusuLog(name=None):
    if not name:
        return getLogger()
    else:
        return getLogger('kusulog.' + name)

class Logger(logging.Logger):
    """
    This Logger class inherits from logging.Logger class.

    It differs from logging.Logger by defaulting to logging to a file
    at level logging.NOTSET. The filename and log level can be controlled
    with $KUSU_LOGFILE and $KUSU_LOGLEVEL environment variables,
    respectively.
    """

    def __init__(self, name="kusulog", filename=""):
        logging.Logger.__init__(self, name)

        # If the filename is not specified, try $KUSU_LOGFILE environment
        # variable, or use the default filename.
        if filename == "":
            try:
                filename = os.environ["KUSU_LOGFILE"]
            except KeyError:
                filename = ""

            if filename == "":
                filename = "kusulog.log"

        # Checks whether the path exists, if not mkdir
        filename = path(filename)
        parent_path = filename.splitpath()[0].abspath()
        if not parent_path.exists():
            parent_path.makedirs()

        # Set default formatter
        self.fmt = logging.Formatter("%(levelname)-8s %(name)s(%(filename)s:%(lineno)d) %(asctime)s %(message)s")

        self.addFileHandler(str(filename))

        # set log level according to $KUSU_LOGLEVEL
        try:
            loglevel = os.environ["KUSU_LOGLEVEL"]
        except KeyError:
            loglevel = ""

        if loglevel not in logging._levelNames:
            loglevel = "INFO"

        self.setLevel(logging.getLevelName(loglevel))

    def addFileHandler (self, file):
        logfileHandler = logging.FileHandler(file)
        logfileHandler.setFormatter(self.fmt)
        self.addHandler(logfileHandler)

    def addSysLogHandler (self, host, port=SYSLOG_UDP_PORT, facility=SysLogHandler.LOG_USER):
        syslogHandler = SysLogHandler((host, port), facility)
        syslogHandler.setFormatter(self.fmt)
        self.addHandler(syslogHandler)

logging.setLoggerClass(Logger)
