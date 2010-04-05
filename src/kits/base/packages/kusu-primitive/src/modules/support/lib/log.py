#!/usr/bin/env python
# $Id: log.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
import tempfile
import logging
from logging.handlers import SysLogHandler, SYSLOG_UDP_PORT
from path import path

def _getLogger(name='primitive'):
    return logging.getLogger(name)

def getPrimitiveLog(name=None):
    if not name:
        return _getLogger()
    else:
        return _getLogger('primitive.' + name)

def shutdown():
    logging.shutdown()

class Logger(logging.Logger):
    """
    This Logger class inherits from logging.Logger class.

    It differs from logging.Logger by defaulting to logging to a file
    at level logging.NOTSET. The filename and log level can be controlled
    with $PRIMITIVE_LOGFILE and $PRIMITIVE_LOGLEVEL environment variables,
    respectively.
    """

    def __init__(self, name="primitive"):
        logging.Logger.__init__(self, name)

        # set default formatter
        self.fmt = logging.Formatter("%(asctime)s %(levelname)s " +
                                     "%(name)s(%(filename)s:" +
                                     "%(lineno)d) %(message)s")
        self.fmt.datefmt = '%Y-%m-%d %H:%M:%S' 

        # set log level according to $PRIMITIVE_LOGLEVEL
        try:
            loglevel = os.environ["PRIMITIVE_LOGLEVEL"]
        except KeyError:
            loglevel = ""

        if loglevel not in logging._levelNames:
            loglevel = "INFO"

        self.setLevel(logging.getLevelName(loglevel))

    def addFileHandler(self, filename="",testing=False):
        """
        Adds a file handler to logger.

        If filename not specified, will try $PRIMITIVE_LOGFILE, else use default of
        /var/log/primitive/primitive.log. File and full path will be created.
        """

        # try $PRIMITIVE_LOGFILE environment variable, or use the default filename
        if filename == "":
            try:
                filename = os.environ["PRIMITIVE_LOGFILE"]
            except KeyError:
                if testing:
                    fd, filename = tempfile.mkstemp(suffix='ulog',dir='/tmp')
                    os.close(fd)
                else:
                    filename = "/var/log/primitive/primitive.log"
            if filename == "":
                if testing:
                    fd, filename= tempfile.mkstemp(suffix='ulog',dir='/tmp')
                    os.close(fd)
                else:
                    filename = "/var/log/primitive/primitive.log"



        # checks whether the path exists, if not mkdir.
        filename = path(filename)
        parent_path = filename.splitpath()[0].abspath()
        if not parent_path.exists():
            parent_path.makedirs()

        logfileHandler = logging.FileHandler(str(filename))
        logfileHandler.setFormatter(self.fmt)
        self.addHandler(logfileHandler)
        return logfileHandler

    def addSysLogHandler(self, host='localhost', port=SYSLOG_UDP_PORT, 
                         facility=SysLogHandler.LOG_USER):
        """
        Adds a syslog handler capable of logging to UNIX system identified by
        (host, port).
        """

        syslogHandler = SysLogHandler((host, port), facility)
        syslogHandler.setFormatter(self.fmt)
        self.addHandler(syslogHandler)
        return syslogHandler
def setLoggerClass():
    logging.setLoggerClass(Logger)
