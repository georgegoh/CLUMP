#!/bin/bash
# $Id$
#
# Kusu specific environment script
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#

export KUSU_ROOT=/opt/kusu
export PYTHONPATH=$KUSU_ROOT/lib64/python:$KUSU_ROOT/lib/python:$PYTHONPATH
export PATH=$KUSU_ROOT/bin:$KUSU_ROOT/sbin:$PATH
export KUSU_DIST=centos
export KUSU_DISTVER=5
export KUSU_DIST_ARCH=x86_64
export KUSU_TMP=/tmp
export KUSU_LOGLEVEL=DEBUG
export KUSU_LOGFILE=/var/log/kusu/kusu.log
export KUSU_MAXLOGSIZE=10485760
export KUSU_MAXLOGNUM=10
export KUSU_EVENT_LOGFILE=/var/log/kusu/kusu-events.log
export KUSU_DB_ENGINE=postgres # options are mysql, postgres
