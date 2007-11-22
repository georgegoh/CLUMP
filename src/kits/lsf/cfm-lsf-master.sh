#!/bin/sh

# This script is call each time the configuration changes on LSF master
# candidates.

. /opt/lsf/conf/profile.lsf

lsadmin reconfig -f
