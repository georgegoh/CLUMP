#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
import logging
import tempfile
from path import path
import kusu.util.log as kusulog

def setUp():
    global tmp_prefix

    tmp_prefix = path(tempfile.mkdtemp(prefix='logtest',
                                       dir=os.environ.get('KUSU_TMP', '/tmp')))

def tearDown():
    global tmp_prefix

    if tmp_prefix.exists():
        tmp_prefix.rmtree()

class TestLogger:
    def setUp(self):
        self.logfilename = tmp_prefix / "kusulog_test.log"
        os.environ['KUSU_LOGFILE'] = self.logfilename
        loggername = "kusulog_test"
        self.myLog = kusulog.getKusuLog(name=loggername)
        self.myLog.addFileHandler()
        self.myLog.setLevel(logging.NOTSET)

        # setting myLog level to NOTSET uses root logger default level WARNING
        logging.getLogger().setLevel(logging.NOTSET)

    def tearDown(self):
        # remove the log file after each test
        if self.logfilename.exists():
            self.logfilename.remove()

        # make sure logging modules are fresh for next test
        reload(logging)
        reload(kusulog)

    def testLog(self):
        """Log message at each logging level with log()."""
        levels = [logging.DEBUG,
                  logging.INFO,
                  logging.WARNING,
                  logging.ERROR,
                  logging.CRITICAL]

        for level in levels:
            fmt = "This is a %s log message" % logging.getLevelName(level)
            self.myLog.log(level, fmt)

            assert findMessage(self.logfilename,
                               logging.getLevelName(level),
                               fmt)

    def testDebug(self):
        """Log message at logging.DEBUG level."""
        fmt = "This is a DEBUG message"
        self.myLog.debug(fmt)
        assert findMessage(self.logfilename,
                           logging.getLevelName(logging.DEBUG),
                           fmt)

    def testInfo(self):
        """Log message at logging.INFO level."""
        fmt = "This is an INFO message"
        self.myLog.info(fmt)
        assert findMessage(self.logfilename,
                           logging.getLevelName(logging.INFO),
                           fmt)

    def testWarning(self):
        """Log message at logging.WARNING level."""
        fmt = "This is a WARNING message"
        self.myLog.warning(fmt)
        assert findMessage(self.logfilename,
                           logging.getLevelName(logging.WARNING),
                           fmt)

    def testError(self):
        """Log message at logging.ERROR level."""
        fmt = "This is a ERROR message"
        self.myLog.error(fmt)
        assert findMessage(self.logfilename,
                           logging.getLevelName(logging.ERROR),
                           fmt)

    def testCritical(self):
        """Log message at logging.CRITICAL level."""
        fmt = "This is a CRITICAL message"
        self.myLog.critical(fmt)
        assert findMessage(self.logfilename,
                           logging.getLevelName(logging.CRITICAL),
                           fmt)

class TestLoggerEnvFilename:
    def setUp(self):
        self.logfilename = tmp_prefix / "kusulog_test_env_filename.log"
        self.loggername = "kusulog_test_env_filename"

    def tearDown(self):
        # remove the log file after each test
        if self.logfilename.exists():
            self.logfilename.remove()

        # unset $KUSU_LOGFILE
        del os.environ['KUSU_LOGFILE']

        # make sure logging modules are fresh for next test
        reload(logging)
        reload(kusulog)

    def testEnvFilename(self):
        """Log to $KUSU_LOGFILE file."""

        # NOTE: setting environ may cause memory leaks on FreeBSD or Mac OS X.
        # See python os module docs for more information.
        os.environ['KUSU_LOGFILE'] = self.logfilename

        # Instantiating kusulog.getKusuLog without the filename forces it to
        # check the $KUSU_LOGFILE environment variable.
        self.myLog = kusulog.getKusuLog(name=self.loggername)
        self.myLog.addFileHandler()

        fmt = "This is a CRITICAL message written to env filename"
        self.myLog.critical(fmt)
        assert findMessage(self.logfilename,
                           logging.getLevelName(logging.CRITICAL),
                           fmt)

    def testEnvFilenameBlank(self):
        """Log to blank $KUSU_LOGFILE file."""

        # NOTE: setting environ may cause memory leaks on FreeBSD or Mac OS X.
        # See python os module docs for more information.
        os.environ['KUSU_LOGFILE'] = ""

        # Instantiating kusulog.getKusuLog without the filename forces it to
        # check the $KUSU_LOGFILE environment variable.
        self.myLog = kusulog.getKusuLog(name=self.loggername)
        self.myLog.addFileHandler()
        self.logfilename = path(self.myLog.handlers[0].baseFilename)

        fmt = "This is a CRITICAL message written to blank env filename"
        self.myLog.critical(fmt)
        assert findMessage(self.logfilename,
                           logging.getLevelName(logging.CRITICAL),
                           fmt)

class TestLoggerEnvLevel:
    levels = [logging.DEBUG,
              logging.INFO,
              logging.WARNING,
              logging.ERROR,
              logging.CRITICAL]

    fmts = dict([(level, "This is a %s message"
                  % logging.getLevelName(level))
                 for level in levels])

    def setUp(self):
        self.logfilename = tmp_prefix / "kusulog_test_env_level.log"
        os.environ['KUSU_LOGFILE'] = self.logfilename
        self.loggername = "kusulog_test_env_level"

    def tearDown(self):
        # remove the log file after each test
        if self.logfilename.exists():
            self.logfilename.remove()

        # unset $KUSU_LOGLEVEL
        del os.environ['KUSU_LOGLEVEL']

        # make sure logging modules are fresh for next test
        reload(logging)
        reload(kusulog)

    def testNotset(self):
        """$KUSU_LOGLEVEL set to NOTSET"""
        os.environ['KUSU_LOGLEVEL'] = "NOTSET"
        self.myLog = kusulog.getKusuLog(name=self.loggername)
        self.myLog.addFileHandler()

        self.logAtAllLevels()

        # When $KUSU_LOGLEVEL is NOTSET, the logging level is determined by
        # the root logger, which defaults to WARNING.
        for level in range(0, 2):
            assert not findMessage(self.logfilename,
                                   logging.getLevelName(self.levels[level]),
                                   self.fmts[self.levels[level]])

        for level in range(2, 5):
            assert findMessage(self.logfilename,
                               logging.getLevelName(self.levels[level]),
                               self.fmts[self.levels[level]])

    def testDebug(self):
        """$KUSU_LOGLEVEL set to DEBUG"""
        os.environ['KUSU_LOGLEVEL'] = "DEBUG"
        self.myLog = kusulog.getKusuLog(name=self.loggername)
        self.myLog.addFileHandler()

        self.logAtAllLevels()

        for level in range(0, 5):
            assert findMessage(self.logfilename,
                               logging.getLevelName(self.levels[level]),
                               self.fmts[self.levels[level]])

    def testInfo(self):
        """$KUSU_LOGLEVEL set to INFO"""
        os.environ['KUSU_LOGLEVEL'] = "INFO"
        self.myLog = kusulog.getKusuLog(name=self.loggername)
        self.myLog.addFileHandler()

        self.logAtAllLevels()

        for level in range(0, 1):
            assert not findMessage(self.logfilename,
                                   logging.getLevelName(self.levels[level]),
                                   self.fmts[self.levels[level]])

        for level in range(1, 5):
            assert findMessage(self.logfilename,
                               logging.getLevelName(self.levels[level]),
                               self.fmts[self.levels[level]])

    def testWarning(self):
        """$KUSU_LOGLEVEL set to WARNING"""
        os.environ['KUSU_LOGLEVEL'] = "WARNING"
        self.myLog = kusulog.getKusuLog(name=self.loggername)
        self.myLog.addFileHandler()

        self.logAtAllLevels()

        for level in range(0, 2):
            assert not findMessage(self.logfilename,
                                   logging.getLevelName(self.levels[level]),
                                   self.fmts[self.levels[level]])

        for level in range(2, 5):
            assert findMessage(self.logfilename,
                               logging.getLevelName(self.levels[level]),
                               self.fmts[self.levels[level]])

    def testError(self):
        """$KUSU_LOGLEVEL set to ERROR"""
        os.environ['KUSU_LOGLEVEL'] = "ERROR"
        self.myLog = kusulog.getKusuLog(name=self.loggername)
        self.myLog.addFileHandler()

        self.logAtAllLevels()

        for level in range(0, 3):
            assert not findMessage(self.logfilename,
                                   logging.getLevelName(self.levels[level]),
                                   self.fmts[self.levels[level]])

        for level in range(3, 5):
            assert findMessage(self.logfilename,
                               logging.getLevelName(self.levels[level]),
                               self.fmts[self.levels[level]])

    def testCritical(self):
        """$KUSU_LOGLEVEL set to CRITICAL"""
        os.environ['KUSU_LOGLEVEL'] = "CRITICAL"
        self.myLog = kusulog.getKusuLog(name=self.loggername)
        self.myLog.addFileHandler()

        self.logAtAllLevels()

        for level in range(0, 4):
            assert not findMessage(self.logfilename,
                                   logging.getLevelName(self.levels[level]),
                                   self.fmts[self.levels[level]])

        for level in range(4, 5):
            assert findMessage(self.logfilename,
                               logging.getLevelName(self.levels[level]),
                               self.fmts[self.levels[level]])

    def testBlank(self):
        """$KUSU_LOGLEVEL set to blank"""
        # This test assumes default level used by kusulog.getKusuLog is
        # INFO
        os.environ['KUSU_LOGLEVEL'] = ""
        self.myLog = kusulog.getKusuLog(name=self.loggername)
        self.myLog.addFileHandler()

        self.logAtAllLevels()

        for level in range(0, 1):
            assert not findMessage(self.logfilename,
                                   logging.getLevelName(self.levels[level]),
                                   self.fmts[self.levels[level]])

        for level in range(1, 5):
            assert findMessage(self.logfilename,
                               logging.getLevelName(self.levels[level]),
                               self.fmts[self.levels[level]])

    def logAtAllLevels(self):
        """Write one message at each log level to the log."""
        for level in self.fmts.keys():
            self.myLog.log(level, self.fmts[level])

def findMessage(logfilename, level, message):
    """
    Grep log file to confirm message logged at corresponding level.

    Arguments:
    level: logging level of message
    message: log message text

    Returns True if message is found logged at level
    """

    rv = False
    f = open(logfilename)
    for line in f:
        if line.find(level) >= 0 and line.find(message) >= 0:
            rv = True
            break
    f.close()

    return rv
