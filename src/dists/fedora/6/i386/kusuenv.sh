#!/usr/bin/bash
# $Id$
#
# Kusu specific environment script
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.
#

export KUSU_ROOT=/opt/kusu
export PYTHONPATH=$KUSU_ROOT/lib/python:$PYTHONPATH
export PATH=$KUSU_ROOT/bin:$KUSU_ROOT/sbin:$PATH