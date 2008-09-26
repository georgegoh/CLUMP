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
# $Id: Makefile 1347 2008-06-11 10:49:27Z hsaliak $
#
include ../../../config.mk

init:
	@cp -pf packages/kusu-core/src/etc/kusu-release packages/kusu-core/src/etc/kusu-release.in
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -e 's%$${KUSU_REVISION}%$(KUSU_REVISION)%g' \
	packages/kusu-core/src/etc/kusu-release.in > packages/kusu-core/src/etc/kusu-release
	@cp -pf packages/kusu-installer/src/lib/welcome.py packages/kusu-installer/src/lib/welcome.py.in
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' \
	packages/kusu-installer/src/lib/welcome.py.in > packages/kusu-installer/src/lib/welcome.py 
	@cp -pf packages/kusu-installer/src/bin/installer packages/kusu-installer/src/bin/installer.in
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' \
	packages/kusu-installer/src/bin/installer.in > packages/kusu-installer/src/bin/installer
	@cp -pf packages/kusu-kitops/src/bin/kitops packages/kusu-kitops/src/bin/kitops.in
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' \
	packages/kusu-kitops/src/bin/kitops.in > packages/kusu-kitops/src/bin/kitops
	@cp -pf packages/kusu-repoman/src/bin/repoman packages/kusu-repoman/src/bin/repoman.in
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' \
	packages/kusu-repoman/src/bin/repoman.in > packages/kusu-repoman/src/bin/repoman
	@cp -pf packages/kusu-repoman/src/bin/repopatch packages/kusu-repoman/src/bin/repopatch.in
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' \
	packages/kusu-repoman/src/bin/repopatch.in > packages/kusu-repoman/src/bin/repopatch

TGZ_ARTIFACTS += init kitinfo
SRPM_ARTIFACTS += init kitinfo
RPM_ARTIFACTS += init kitinfo
ISO_ARTIFACTS += init kitinfo


# Dynamically pull the Release/Version from the spec file; these values
# cannot be hardcoded!


# include user-defined kit-specific information
include config.mk
include ../kits.mk

BASE_KIT_VERSION_STR=$(shell grep "^Version: " SPECS/$(PKG_KIT_SPEC) | awk '{print $$2}')
BASE_KIT_RELEASE_STR=$(shell grep "^Release: " SPECS/$(PKG_KIT_SPEC) | awk '{print $$2}')

COMPONENT_BASE_INSTALLER_VERSION_STR=$(shell grep "^Version: " SPECS/$(PKG_COMPONENT_BASE_INSTALLER_SPEC) | awk '{print $$2}')
COMPONENT_BASE_INSTALLER_RELEASE_STR=$(shell grep "^Release: " SPECS/$(PKG_COMPONENT_BASE_INSTALLER_SPEC) | awk '{print $$2}')

COMPONENT_BASE_NODE_VERSION_STR=$(shell grep "^Version: " SPECS/$(PKG_COMPONENT_BASE_NODE_SPEC) | awk '{print $$2}')
COMPONENT_BASE_NODE_RELEASE_STR=$(shell grep "^Release: " SPECS/$(PKG_COMPONENT_BASE_NODE_SPEC) | awk '{print $$2}')

COMPONENT_GNOME_DESKTOP_VERSION_STR=$(shell grep "^Version: " SPECS/$(PKG_COMPONENT_GNOME_DESKTOP_SPEC) | awk '{print $$2}')
COMPONENT_GNOME_DESKTOP_RELEASE_STR=$(shell grep "^Release: " SPECS/$(PKG_COMPONENT_GNOME_DESKTOP_SPEC) | awk '{print $$2}')

.PHONY: kitinfo
kitinfo:
	@sed -e 's%$${COMPONENT_BASE_INSTALLER_VERSION_STR}%$(COMPONENT_BASE_INSTALLER_VERSION_STR)%g' \
    -e 's%$${COMPONENT_BASE_INSTALLER_RELEASE_STR}%$(COMPONENT_BASE_INSTALLER_RELEASE_STR)%g' \
    -e 's%$${COMPONENT_BASE_NODE_VERSION_STR}%$(COMPONENT_BASE_NODE_VERSION_STR)%g' \
    -e 's%$${COMPONENT_BASE_NODE_RELEASE_STR}%$(COMPONENT_BASE_NODE_RELEASE_STR)%g' \
    -e 's%$${COMPONENT_GNOME_DESKTOP_VERSION_STR}%$(COMPONENT_GNOME_DESKTOP_VERSION_STR)%g' \
    -e 's%$${COMPONENT_GNOME_DESKTOP_RELEASE_STR}%$(COMPONENT_GNOME_DESKTOP_RELEASE_STR)%g' \
    -e 's%$${BASE_KIT_VERSION_STR}%$(BASE_KIT_VERSION_STR)%g' \
    -e 's%$${BASE_KIT_RELEASE_STR}%$(BASE_KIT_RELEASE_STR)%g' \
	packages/kit-base/kitinfo.in >packages/kit-base/kitinfo

