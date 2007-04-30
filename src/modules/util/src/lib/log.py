#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

__version__ = "$Rev:$"

import os
import logging
from path import path

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

        # Set level of root logger to NOTSET
        # in order to control the log level from kusu.util.log.
        rootlog = logging.getLogger()
        rootlog.setLevel(logging.NOTSET)

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

        self.addFileHandler(str(filename))

        # set log level according to $KUSU_LOGLEVEL
        try:
            loglevel = os.environ["KUSU_LOGLEVEL"]
        except KeyError:
            loglevel = ""

        if loglevel not in logging._levelNames:
            loglevel = "INFO"

        self.setLevel(logging.getLevelName(loglevel))

    def addFileHandler (self, file, fmt="%(levelname)-8s %(name)s(%(filename)s:%(lineno)d) %(asctime)s %(message)s"):
        logfileHandler = logging.FileHandler(file)
        flogfmt = logging.Formatter(fmt)
        logfileHandler.setFormatter(flogfmt)
        self.addHandler(logfileHandler)

#        self.critical("Kusu logger online")
#        self.debug("\n\tkusulog at %x\n\t%s logger at %x\n\troot logger at %x"
#                    % (id(self), name, id(logging.getLogger(name)),
#                        id(logging.getLogger())))
#        self.debug("\n\tkloghandler at %x\n\tklogfmt at %x"
#                    % (id(kloghandler), id(klogfmt)))
