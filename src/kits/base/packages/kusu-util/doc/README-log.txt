$Id$

Kusu log module mini-HOWTO
==========================

This module is basically the default Python logging module. By default, each
object logs to the same file, controlled by $KUSU_LOGFILE environment variable,
defaulting to kusulog.log.

The logging system provides five levels of log messages. In increasing
severity, they are:
 * DEBUG
 * INFO
 * WARNING
 * ERROR
 * CRITICAL

The logging level is controlled by the $KUSU_LOGLEVEL environment variable and
defaults to INFO. This means all messages at level INFO or above are logged,
while messages with level below INFO are ignored.

The Python logging system allows naming of loggers. Requesting a logger by
name from the logging system returns that logger or creates one if it doesn't
already exist. The Kusu log module defaults to a logger called 'kusulog'.

You are encouraged to name your loggers. A good system is to provide your
module or subsystem name. This permits the filtering of log messages based
on where they originate.

Functions
=========

Module functions:

getKusuLog(name=None)
Returns kusu.util.log.Logger object. If the logger does not exist it is
created. If name is None, returns object named 'kusulog', the main logger. If a
name is specified it is appended to 'kusulog'. For example,
getKusuLog('partition') returns 'kusulog.partition'.

_getLogger(name='kusulog')
Thin wrapper around logging.getLogger().

shutdown()
Thin wrapper around logging.shutdown(). Informs the logging system to perform
an orderly shutdown by flushing and closing all handlers.

kusu.util.log.Logger object functions:

addFileHandler(self, filename="")
Adds a file handler to the logger. If filename is not specified, the
environment variable $KUSU_LOGFILE is used. If $KUSU_LOGFILE is not set or
empty, the default '/tmp/kusu/kusu.log' is used. If the complete path
specified does not exist, it is created.

addSysLogHandler(self, host='localhost', port=SYSLOG_UDP_PORT, 
                 facility=SysLogHandler.LOG_USER)
Adds a syslog handler to the logger. The handler will write log messages to
the syslog on a remote UNIX machine identified by (host, port). Defaults to
localhost.

Brief Example
=============

import kusu.util.log as kusulog

# kl.name will be 'kusulog'
kl = kusulog.getKusuLog()

# we need to add a file handler to the topmost logger
# no arguments defaults to logging to /tmp/kusu/kusu.log
kl.addFileHandler()

# there are five methods for logging at each level
kl.debug('This is DEBUG message #%s' % 1)
kl.info('This is INFO message #%s' % 1)
kl.warning('This is WARNING message #%s' % 1)
kl.error('This is ERROR message #%s' % 1)
kl.critical('This is CRITICAL message #%s' % 1)

# if we want to log to syslog
kl.addSysLogHandler()

# adding another logger as a child of kusulog
partitionlog = kusulog.getKusuLog('partition') # partitionlog.name will be
                                               # 'kusulog.partition'

# partitionlog will log to all handlers in partitionlog and kl
partitionlog.addFileHandler('/path/to/partition/log')
kl.error('An error from kl')
partitionlog.critical('Hi, from partitionlog')

# $ cat /tmp/kusu/kusu.log
# ERROR kusulog An error from kl
# CRITICAL kusulog.partition Hi, from partitionlog
# $ cat syslog
# ERROR kusulog An error from kl
# CRITICAL kusulog.partition Hi, from partitionlog
# $ cat /path/to/partition/log
# CRITICAL kusulog.partition Hi, from partitionlog

# when application is terminating
kusulog.shutdown()

# End example

More Information
================

The class kusu.util.log.Logger inherits from class logging.Logger, so all
methods in logging.Logger are accessible. See logging module Python
documentation for more details.
