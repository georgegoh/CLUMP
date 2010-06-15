#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
import logging
from logging.handlers import SysLogHandler, SYSLOG_UDP_PORT, RotatingFileHandler
from path import path
from pwd import getpwnam


DEFAULT_MAX_LOG_SIZE = 10485760    # 10 MB
DEFAULT_MAX_LOG_NUM = 10


def _getLogger(name='kusu'):
    return logging.getLogger(name)

def getKusuLog(name=None):
    if not name:
        return _getLogger()
    else:
        return _getLogger('kusu.' + name)

def getPrimitiveLog():
        return _getLogger('primitive')

def getKusuEventLog():
        
    kl = _getLogger('kusu.events')
    
    # set event log formatter
    kl.fmt = logging.Formatter("%(asctime)s %(levelname)s " +
                               "%(name)s (%(process)d) " +
                               "%(message)s")    
    kl.fmt.datefmt = '%Y-%m-%d %H:%M:%S' 
    
    # Note: the event logger also inherits
    # the root logger's handler    
    if not kl.handlers:
        try:
            eventLog = os.environ["KUSU_EVENT_LOGFILE"]
        except KeyError:
            eventLog = '/var/log/kusu/kusu-events.log'

        # Check if we are root, if not just open /dev/null
        if os.geteuid() != 0:
           eventLog = '/dev/null'
    
        kl.addFileHandler(eventLog)

    return kl

def initKusuLogFile(logPath):

    # Create the log directory if it doesn't exist
    logPath = path(logPath)
    parentPath = logPath.splitpath()[0].abspath()
    if not parentPath.exists():
        parentPath.makedirs()

    logPath.touch()
    logPath.chmod(0644)
    
    # If we're root, change the log ownership to the apache user.
    # If it's any other user, then create the log as that user.
    if os.geteuid() == 0:
        try:
            uinfo = getpwnam('apache')
            uid = uinfo[2]
            gid = uinfo[3]
            logPath.chown(uid, gid)
        except KeyError:
            # If we reach this point, we must be in Install mode.
            # Just ignore.
            pass

def shutdown():
    logging.shutdown()

class KusuRotatingFileHandler(RotatingFileHandler):
    """
    This Log Handler class inherits from logging.handlers.RotatingFileHandler
    
    It differs from RotatingFileHandler by setting the log file ownership 
    to the 'apache' user and the permissions to 0644 when rollover occurs 
    only if we're running as the root user. 
    """
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None):
        self.filename = filename
        RotatingFileHandler.__init__(self, filename, mode, maxBytes, backupCount)
    
    def doRollover(self):
        RotatingFileHandler.doRollover(self)
        initKusuLogFile(self.filename)

class Logger(logging.Logger):
    """
    This Logger class inherits from logging.Logger class.

    It differs from logging.Logger by defaulting to logging to a file
    at level logging.NOTSET. The filename and log level can be controlled
    with $KUSU_LOGFILE and $KUSU_LOGLEVEL environment variables,
    respectively.
    """
    # Default rotating log options
    #    Log size can be modified using KUSU_MAXLOGSIZE env variable
    #    Log number can be modified using KUSU_MAXLOGNUM env variable
    LogMode = 'a'


    def __init__(self, name="kusu"):
        logging.Logger.__init__(self, name)

        # set default formatter
        self.fmt = logging.Formatter("%(asctime)s %(levelname)s " +
                                     "%(name)s (%(filename)s:" +
                                     "%(lineno)d) %(message)s")
        self.fmt.datefmt = '%Y-%m-%d %H:%M:%S' 

        # set log level according to $KUSU_LOGLEVEL
        try:
            loglevel = os.environ["KUSU_LOGLEVEL"]
        except KeyError:
            loglevel = ""

        if loglevel not in logging._levelNames:
            loglevel = "INFO"

        self.setLevel(logging.getLevelName(loglevel))

    def addFileHandler(self, filename=""):
        """
        Adds a file handler to logger.

        If filename not specified, will try $KUSU_LOGFILE, else use default of
        /var/log/kusu/kusu.log. File and full path will be created.
        """

        # try $KUSU_LOGFILE environment variable, or use the default filename
        if filename == "":
            try:
                filename = os.environ["KUSU_LOGFILE"]
            except KeyError:
                filename = "/var/log/kusu/kusu.log"
            if filename == "":
                filename = "/var/log/kusu/kusu.log"

        # handle devices, e.g., /dev/tty3
        if filename.startswith('/dev'):
            logfileHandler = logging.FileHandler(str(filename))
            logfileHandler.setFormatter(self.fmt)
            self.addHandler(logfileHandler)
        else:
            # handle regular files
            
            # Ensure file has proper ownership and permissions
            initKusuLogFile(filename)
    
            # Get log size and number from the environment, or use the
            # default 
            try:
                logsize = int(os.environ["KUSU_MAXLOGSIZE"])
            except (KeyError,ValueError), e:
                logsize = DEFAULT_MAX_LOG_SIZE
                 
            try:
                lognum = int(os.environ["KUSU_MAXLOGNUM"])
            except (KeyError,ValueError), e:
                lognum = DEFAULT_MAX_LOG_NUM
    
            logfileHandler = KusuRotatingFileHandler(str(filename), 
                                    self.LogMode, logsize, lognum)
            
            logfileHandler.setFormatter(self.fmt)
            self.addHandler(logfileHandler)

    def addSysLogHandler(self, host='localhost', port=SYSLOG_UDP_PORT, 
                         facility=SysLogHandler.LOG_USER):
        """
        Adds a syslog handler capable of logging to UNIX system identified by
        (host, port).
        """

        syslogHandler = SysLogHandler((host, port), facility)
        syslogHandler.setFormatter(self.fmt)
        self.addHandler(syslogHandler)

logging.setLoggerClass(Logger)
