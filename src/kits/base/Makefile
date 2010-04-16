# Copyright (C) 2010 Platform Computing Inc
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
# $Id: Makefile 3501 2010-02-10 06:30:36Z binxu $
#
include ../../../config.mk

.PHONY: sles rhel
sles:
	make iso KIT="base" KUSU_BUILD_DIST=sles KUSU_BUILD_DISTVER=10 KUSU_BUILD_ARCH=x86_64
rhel:
	make iso KIT="base" KUSU_BUILD_DIST=rhel KUSU_BUILD_DISTVER=5 KUSU_BUILD_ARCH=x86_64

init:
	@mkdir -p BUILD RPMS SOURCES SPECS SRPMS
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -e 's%$${KUSU_REVISION}%$(KUSU_REVISION)%g' \
	-e 's%$${KUSU_RELEASE_NAME}%$(KUSU_RELEASE_NAME)%g' -i packages/kusu-release/src/kusu-release
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' \
	-e 's%$${KUSU_RELEASE_NAME}%$(KUSU_RELEASE_NAME)%g' -i packages/kusu-installer/src/lib/welcome.py
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' \
	-e 's%$${KUSU_RELEASE_NAME}%$(KUSU_RELEASE_NAME)%g' -i packages/kusu-installer/src/lib/kits.py
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g'  -e 's%$${KUSU_REVISION}%$(KUSU_REVISION)%g' \
	-e 's%$${KUSU_RELEASE_NAME}%$(KUSU_RELEASE_NAME)%g' -i packages/kusu-installer/src/bin/installer
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-kitops/src/bin/kusu-kitops
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-repoman/src/bin/kusu-repoman
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-node/sbin/updatenic.py
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/sbin/kusu-netedit.py
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/sbin/kusu-nghosts.py
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/sbin/kusu-addhost.py
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-core/src/lib/app.py
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-core/src/bin/kusu-register.py
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-repoman/src/bin/kusu-repopatch
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -e 's%$${KUSU_REVISION}%$(KUSU_REVISION)%g' \
	-e 's%$${KUSU_RELEASE_NAME}%$(KUSU_RELEASE_NAME)%g' -i packages/kusu-base-installer/sbin/S03KusuMotd.rc.py
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-core/src/lib/database.py
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-shell/src/lib/kusu_shell_app.py
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-shell/src/bin/kusu
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-migrate/src/sbin/kusu-migrate

	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-shell/src/man/kusu.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-node/man/updatenic.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-migrate/src/man/kusu-migrate.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-kit-install/src/man/kusu-kit-install.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/kusu-kitops.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/kusu-netedit.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/sqlrunner.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/kusu-cfmsync.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/kusu-ngedit.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/kusu-genconfig.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/kusu-nghosts.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/cfmd.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/kusu-buildinitrd.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/kusu-addhost.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/cfmclient.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/kusu-buildimage.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/kusu-repoman.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/kusu-boothost.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-base-installer/man/kusu-repopatch.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-nodeinstaller-patchfiles/man/genupdatesimg.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-net-tool/man/kusu-net-tool.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-autoinstall/src/man/autogen.8
	@sed -e 's%$${VERSION_STR}%$(KUSU_VERSION)%g' -i packages/kusu-appglobals-tool/src/man/kusu-appglobals-tool.8

ifeq ($(KUSU_DISTRO_NAME), sles)
	@echo 'Removing EPEL and Fedora packages from source tree'
	@find ./RPMS -type f -name '*.el5.i386.rpm' | xargs rm -f
	@find ./RPMS -type f -name '*.el5.x86_64.rpm' | xargs rm -f
	@find ./RPMS -type f -name '*.fc9.i386.rpm' | xargs rm -f
	@find ./RPMS -type f -name '*.fc9.x86_64.rpm' | xargs rm -f
endif

TGZ_ARTIFACTS += init kitinfo
SRPM_ARTIFACTS += init kitinfo
RPM_ARTIFACTS += init kitinfo
ISO_ARTIFACTS += init kitinfo


# Dynamically pull the Release/Version from the spec file; these values
# cannot be hardcoded!


# include user-defined kit-specific information
ifeq ($(KUSU_DISTRO_NAME), sles)
include config.mk.sles
KITINFO_TEMPLATE=kitinfo.in.sles
endif
ifeq ($(KUSU_DISTRO_NAME), opensuse)
include config.mk.opensuse
KITINFO_TEMPLATE=kitinfo.in.sles
endif
ifeq ($(KUSU_DISTRO_NAME), centos)
include config.mk
BASE_KIT_COMPONENT_OS_NAME_STR=rhelfamily
KITINFO_TEMPLATE=kitinfo.in
endif
ifeq ($(KUSU_DISTRO_NAME), scientificlinux)
include config.mk
BASE_KIT_COMPONENT_OS_NAME_STR=rhelfamily
KITINFO_TEMPLATE=kitinfo.in
endif
ifeq ($(KUSU_DISTRO_NAME), scientificlinuxcern)
include config.mk
BASE_KIT_COMPONENT_OS_NAME_STR=rhelfamily
KITINFO_TEMPLATE=kitinfo.in
endif
ifeq ($(KUSU_DISTRO_NAME), rhel)
include config.mk
BASE_KIT_COMPONENT_OS_NAME_STR=rhelfamily
KITINFO_TEMPLATE=kitinfo.in
endif

include ../kits.mk

ifndef BASE_KIT_COMPONENT_OS_NAME_STR
BASE_KIT_COMPONENT_OS_NAME_STR=$(KUSU_DISTRO_NAME)
endif

BASE_KIT_COMPONENT_OS_MAJOR_STR=$(KUSU_DISTRO_VERSION)
BASE_KIT_COMPONENT_OS_ARCH_STR=$(KUSU_DISTRO_ARCH)

ifdef KUSU_DISTRO_VERSION_MINOR
BASE_KIT_COMPONENT_OS_MINOR_STR=$(KUSU_DISTRO_VERSION_MINOR)
else
BASE_KIT_COMPONENT_OS_MINOR_STR=*
endif

BASE_KIT_VERSION_STR=$(KIT_VERSION)
BASE_KIT_RELEASE_STR=$(KIT_RELEASE)
BASE_KIT_ARCH_STR=$(shell uname -i)

COMPONENT_BASE_INSTALLER_VERSION_STR=$(shell grep "^Version: " SPECS/$(PKG_COMPONENT_BASE_INSTALLER_SPEC) | awk '{print $$2}')
COMPONENT_BASE_INSTALLER_RELEASE_STR=$(shell grep "^Release: " SPECS/$(PKG_COMPONENT_BASE_INSTALLER_SPEC) | awk '{print $$2}')

COMPONENT_BASE_NODE_VERSION_STR=$(shell grep "^Version: " SPECS/$(PKG_COMPONENT_BASE_NODE_SPEC) | awk '{print $$2}')
COMPONENT_BASE_NODE_RELEASE_STR=$(shell grep "^Release: " SPECS/$(PKG_COMPONENT_BASE_NODE_SPEC) | awk '{print $$2}')

COMPONENT_GNOME_DESKTOP_VERSION_STR=$(shell grep "^Version: " SPECS/$(PKG_COMPONENT_GNOME_DESKTOP_SPEC) | awk '{print $$2}')
COMPONENT_GNOME_DESKTOP_RELEASE_STR=$(shell grep "^Release: " SPECS/$(PKG_COMPONENT_GNOME_DESKTOP_SPEC) | awk '{print $$2}')

COMPONENT_ICR_VERSION_STR=$(shell grep "^Version: " SPECS/$(PKG_COMPONENT_ICR_SPEC) | awk '{print $$2}')
COMPONENT_ICR_RELEASE_STR=$(shell grep "^Release: " SPECS/$(PKG_COMPONENT_ICR_SPEC) | awk '{print $$2}')

.PHONY: kitinfo
kitinfo:
	@sed -e 's%$${COMPONENT_BASE_INSTALLER_VERSION_STR}%$(COMPONENT_BASE_INSTALLER_VERSION_STR)%g' \
    -e 's%$${COMPONENT_BASE_INSTALLER_RELEASE_STR}%$(COMPONENT_BASE_INSTALLER_RELEASE_STR)%g' \
    -e 's%$${COMPONENT_BASE_NODE_VERSION_STR}%$(COMPONENT_BASE_NODE_VERSION_STR)%g' \
    -e 's%$${COMPONENT_BASE_NODE_RELEASE_STR}%$(COMPONENT_BASE_NODE_RELEASE_STR)%g' \
    -e 's%$${COMPONENT_GNOME_DESKTOP_VERSION_STR}%$(COMPONENT_GNOME_DESKTOP_VERSION_STR)%g' \
    -e 's%$${COMPONENT_GNOME_DESKTOP_RELEASE_STR}%$(COMPONENT_GNOME_DESKTOP_RELEASE_STR)%g' \
    -e 's%$${COMPONENT_ICR_VERSION_STR}%$(COMPONENT_ICR_VERSION_STR)%g' \
    -e 's%$${COMPONENT_ICR_RELEASE_STR}%$(COMPONENT_ICR_RELEASE_STR)%g' \
    -e 's%$${BASE_KIT_COMPONENT_OS_NAME_STR}%$(BASE_KIT_COMPONENT_OS_NAME_STR)%g' \
    -e 's%$${BASE_KIT_COMPONENT_OS_MAJOR_STR}%$(BASE_KIT_COMPONENT_OS_MAJOR_STR)%g' \
    -e 's%$${BASE_KIT_COMPONENT_OS_MINOR_STR}%$(BASE_KIT_COMPONENT_OS_MINOR_STR)%g' \
    -e 's%$${BASE_KIT_COMPONENT_OS_ARCH_STR}%$(BASE_KIT_COMPONENT_OS_ARCH_STR)%g' \
    -e 's%$${BASE_KIT_VERSION_STR}%$(BASE_KIT_VERSION_STR)%g' \
    -e 's%$${BASE_KIT_RELEASE_STR}%$(BASE_KIT_RELEASE_STR)%g' \
    -e 's%$${BASE_KIT_ARCH_STR}%$(BASE_KIT_ARCH_STR)%g' \
	packages/kit-base/$(KITINFO_TEMPLATE) >packages/kit-base/kitinfo

