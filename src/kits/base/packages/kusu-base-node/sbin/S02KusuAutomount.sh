#!/bin/bash
# $Id: automount.sh 2435 2007-10-03 10:19:46Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

echo "`hostname`: `date`" >> /tmp/cfm_automount_plugin.log
/etc/init.d/autofs restart >> /tmp/cfm_automount_plugin.log
echo

