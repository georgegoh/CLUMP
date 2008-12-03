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

# global kusu build params.
ifdef KUSU_BUILD_DIST
KUSU_DISTRO_NAME=$(KUSU_BUILD_DIST)
else
KUSU_DISTRO_NAME=centos
endif
ifdef KUSU_BUILD_DISTVER
KUSU_DISTRO_VERSION=$(KUSU_BUILD_DISTVER)
else
KUSU_DISTRO_VERSION=5
endif
ifdef KUSU_BUILD_ARCH
KUSU_DISTRO_ARCH=$(KUSU_BUILD_ARCH)
else
KUSU_DISTRO_ARCH=x86_64
endif

KUSU_DISTRO_SRC=/mnt/share/$(KUSU_DISTRO_NAME)-$(KUSU_DISTRO_VERSION)-$(KUSU_DISTRO_ARCH)

KUSU_TOPDIR=`pwd`
KUSU_RPM_TMPPATH=/tmp/kusu

KUSU_RELEASE_NAME=Parrot Fish
KUSU_VERSION = 1.2
KUSU_REVISION = @KUSU_REVISION@

# lists of kits to build
KUSU_KITS_LISTS=\
base

ARCH = $(shell uname -i)
