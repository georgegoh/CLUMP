# Copyright (C) 2007 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
# $Id$
#

# global kusu build params.
KUSU_DISTRO_SRC=/mnt/share/@KUSU_BUILD_DIST@-@KUSU_BUILD_DISTVER@-@KUSU_BUILD_ARCH@
KUSU_DISTRO_NAME=@KUSU_BUILD_DIST@
KUSU_DISTRO_VERSION=@KUSU_BUILD_DISTVER@
KUSU_DISTRO_ARCH=@KUSU_BUILD_ARCH@
KUSU_TOPDIR=`pwd`
KUSU_RPM_TMPPATH=/tmp/kusu

KUSU_VERSION = 0.10
KUSU_REVISION = $(shell svn info $(KUSU_TOPDIR) | grep "Last Changed Rev" | awk '{print $$4}')

# lists of kits to build
KUSU_KITS_LISTS=\
base

