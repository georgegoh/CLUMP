#!/bin/bash
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

# runlevel 3
chkconfig --list autofs | awk '{print $5}' | grep "off"
AUTOFS_3_STATE=$?

# runlevel 5
chkconfig --list autofs | awk '{print $7}' | grep "off"
AUTOFS_5_STATE=$?

# Comment this line and uncomment the following to re-enable autofs support
AUTOFS_ENABLED=0

# AUTOFS_ENABLED=$(( $AUTOFS_3_STATE | $AUTOFS_5_STATE ))

if [ $AUTOFS_ENABLED -ne 0 ]; then
    echo "`hostname`: `date`" >> /tmp/cfm_automount_plugin.log
    service autofs restart >> /tmp/cfm_automount_plugin.log
    echo
fi
