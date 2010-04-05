#!/bin/bash
# $Id: kusuenv.sh 3665 2008-10-29 10:57:52Z kunalc $
#
# Kusu specific environment script
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#

export KUSU_ROOT=/opt/kusu
export PRIMITIVE_ROOT=/opt/primitive
export PYTHONPATH=$KUSU_ROOT/lib64/python:$KUSU_ROOT/lib/python:$PYTHONPATH
export PYTHONPATH=$PRIMITIVE_ROOT/lib64/python2.4/site-packages:$PRIMITIVE_ROOT/lib/python2.4/site-packages:$PYTHONPATH
export PATH=$KUSU_ROOT/bin:$KUSU_ROOT/sbin:$PATH

#export KUSU_DIST=centos
#export KUSU_DISTVER=5
#export KUSU_DIST_ARCH=x86_64
if [ -f /etc/fedora-release ]; then
    export KUSU_DIST=fedora
    [[ `head -n 1 /etc/fedora-release` =~ '[0-9]+' ]]
    export KUSU_DISTVER=$BASH_REMATCH
elif [ -f /etc/redhat-release ]; then
    KUSU_DIST=`head -n 1 /etc/redhat-release | awk '{print $1}'`
    case "$KUSU_DIST" in 
    "Red" )
        export KUSU_DIST=rhel
    ;;
    "Scientific" )
        export KUSU_DIST=scientificlinux
    ;;
    * )
        export KUSU_DIST=centos
    ;;
    esac
    [[ `head -n 1 /etc/redhat-release` =~ '[0-9]+' ]]
    export KUSU_DISTVER=$BASH_REMATCH
elif [ -f /etc/SuSE-release ]; then
    KUSU_DIST=`head -n 1 /etc/SuSE-release | awk '{print $1}'`
    case "$KUSU_DIST" in 
    "SUSE" )
        export KUSU_DIST=sles
    ;;
    "openSUSE" )
        export KUSU_DIST=opensuse
    ;;
    esac
    export KUSU_DISTVER=`grep VERSION /etc/SuSE-release | awk -F' = ' '{print $2}' | sed 's/\.//'`
fi
if [ -z "$KUSU_DIST_ARCH" ]; then
    export KUSU_DIST_ARCH=`uname -m | sed s/i[3456]86/i386/`
fi

export KUSU_TMP=/tmp
export KUSU_LOGLEVEL=DEBUG
export KUSU_LOGFILE=/var/log/kusu/kusu.log
export KUSU_MAXLOGSIZE=10485760
export KUSU_MAXLOGNUM=10
export KUSU_EVENT_LOGFILE=/var/log/kusu/kusu-events.log
export KUSU_DB_ENGINE=postgres # options are mysql, postgres
export MANPATH=$MANPATH:/opt/kusu/man
