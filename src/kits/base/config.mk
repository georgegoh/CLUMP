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

### Kit Configuration File
#
# Section 1: Kit Metadata
#
# Kit metadata consists of the following variables that must be set:
#
#   KIT_PROPER_NAME - the "proper" name of the kit. For instance,
#                     "Kusu Runtime" (minus the quotes).
#          KIT_NAME - This is converted to all lowercase from the
#                     KIT_PROPER_NAME variable, then used in determining
#                     generated file names (such as RPM, ISO, etc). This
#                     variable can be overridden.
#       KIT_VERSION - the version of this kit.
#       KIT_RELEASE - the release of this kit.
#          KIT_ARCH - the CPU architecture this kit is for. Can be
#                     set to $(ARCH) which contains the current system's
#                     CPU architecture. This variable can be overriden.
#
KIT_PROPER_NAME = base
KIT_VERSION = $(shell grep "^Version: " SPECS/kit-base.spec | awk '{print $$2}')
KIT_RELEASE = $(shell grep "^Release: " SPECS/kit-base.spec | awk '{print $$2}')
KIT_NAME = $(shell echo $(KIT_PROPER_NAME) | tr A-Z a-z)
KIT_ARCH = $(shell uname -i)

#
# Section 2: Package Definitions
#
# Define all the packages to be included in the kit. A package is defined
# in a series of variables with the same prefix unique to this package.
# The prefix is added to the KIT_PKGS variable in order to be included in
# the Makefile's targets. The mandatory properties are:
#
#      {PREFIX}_NAME - the name of this package, used for determining
#                      filenames (RPM, SRPM, spec file, etc).
#   {PREFIX}_VERSION - the version of this package.
#   {PREFIX}_RELEASE - the release of this package.
#      {PREFIX}_ARCH - the CPU architecture this package is compiled for.
#                      Can be set to $(ARCH), the current CPU architecture
#                      or can be manually overridden.
#
# Each package must also specify its one source from which the package is
# generated. Do not define more than one of the following for the same
# package:
#
#     {PREFIX}_SPEC - this package is generated from a spec file. The
#                     filename is stored in this variable. The value in
#                     $(SPECDIR) will be prepended to this variable;
#                     $(SPECDIR) defaults to SPECS/
#   {PREFIX}_PARENT - this package is generated as a sub-package from
#                     another package, when a spec file is built or an SRPM
#                     is rebuilt. This variable should store the {PREFIX}
#                     of its parent's package definition. PARENT-type
#                     packages need only their NAME defined; the VERSION,
#                     RELEASE and ARCH are obtained from the parent.
#     {PREFIX}_SRPM - this package is rebuilt from a source RPM. This
#                     variable stores the SRPM filename.
#      {PREFIX}_RPM - this package is already a compiled RPM. This variable
#                     stores the RPM filename.
#
# Below is an example definition of a Kusu Kitops RPM:
#
# KIT_PKGS += PKG_KUSU_KITOPS          # add this package to KIT_PKGS
# PKG_KUSU_KITOPS_NAME = kusu-kitops
# PKG_KUSU_KITOPS_VERSION = 0.6
# PKG_KUSU_KITOPS_RELEASE = 0
# PKG_KUSU_KITOPS_ARCH = $(ARCH)
# PKG_KUSU_KITOPS_SPEC = $(PKG_KUSU_KITOPS_NAME).spec
#
# Let's assume the fictitious Kit Checker tool is a sub-package built
# from the Kusu Kitops RPM:
#
# KIT_PKGS += PKG_KUSU_KIT_CHECK
# PKG_KUSU_KIT_CHECK_NAME = kusu-kit-check       # no need to define version
# PKG_KUSU_KIT_CHECK_PARENT = PKG_KUSU_KITOPS    # note the assigned value
#                                                # is the parent's prefix
#

KIT_PKGS += PKG_KIT
PKG_KIT_SPEC = kit-base.spec
PKG_KIT_SOURCES = docs plugins kitinfo

KIT_PKGS += PKG_COMPONENT_BASE_INSTALLER
PKG_COMPONENT_BASE_INSTALLER_SPEC = component-base-installer.spec

KIT_PKGS += PKG_COMPONENT_BASE_NODE
PKG_COMPONENT_BASE_NODE_SPEC = component-base-node.spec
PKG_COMPONENT_BASE_NODE_SOURCES = src/doc src/libexec

KIT_PKGS += PKG_COMPONENT_GNOME_DESKTOP
PKG_COMPONENT_GNOME_DESKTOP_SPEC = component-gnome-desktop.spec

KIT_PKGS += PKG_COMPONENT_ICR
PKG_COMPONENT_ICR_SPEC = component-icr-facilitator.spec
PKG_COMPONENT_ICR_SOURCES = etc

# Kusu Base installer package.
KIT_PKGS += PKG_BASE_INSTALLER
PKG_BASE_INSTALLER_SPEC = kusu-base-installer.spec
PKG_BASE_INSTALLER_SOURCES = lib sbin bin man portal etc po tftpboot firstboot libexec

# Kusu Base node package.
KIT_PKGS += PKG_BASE_NODE
PKG_BASE_NODE_SPEC = kusu-base-node.spec
PKG_BASE_NODE_SOURCES = doc cfm etc lib sbin man

# Kusu Repoman package.
KIT_PKGS += PKG_REPOMAN
PKG_REPOMAN_SPEC = kusu-repoman.spec
PKG_REPOMAN_SOURCES = doc src/bin src/lib src/etc
#PKG_REPOMAN_SOURCES = src setup.py

# Kusu Boot package.
KIT_PKGS += PKG_BOOT
PKG_BOOT_SPEC = kusu-boot.spec
PKG_BOOT_SOURCES = doc src/bin src/lib
#PKG_BOOT_SOURCES = src setup.py

# Kusu Buildkit package.
KIT_PKGS += PKG_BUILDKIT
PKG_BUILDKIT_SPEC = kusu-buildkit.spec
PKG_BUILDKIT_SOURCES = doc src/bin src/lib src/etc
#PKG_BUILDKIT_SOURCES = src setup.py

# Kusu Core package.
KIT_PKGS += PKG_CORE
PKG_CORE_SPEC = kusu-core.spec
PKG_CORE_SOURCES = doc src/bin src/lib src/etc

# Kusu Shell package.
#KIT_PKGS += PKG_SHELL
#PKG_SHELL_SPEC = kusu-shell.spec
#PKG_SHELL_SOURCES = doc src/bin src/lib src/plugins src/man

# Kusu Driverpatch package.
KIT_PKGS += PKG_DRIVERPATCH
PKG_DRIVERPATCH_SPEC = kusu-driverpatch.spec
PKG_DRIVERPATCH_SOURCES = doc src/bin src/lib
#PKG_DRIVERPATCH_SOURCES = src setup.py

# Kusu Hardware package.
KIT_PKGS += PKG_HARDWARE
PKG_HARDWARE_SPEC = kusu-hardware.spec
PKG_HARDWARE_SOURCES = doc src/lib
#PKG_HARDWARE_SOURCES = src setup.py

# Kusu Kitops package.
KIT_PKGS += PKG_KITOPS
PKG_KITOPS_SPEC = kusu-kitops.spec
PKG_KITOPS_SOURCES = doc src/bin src/lib src/etc
#PKG_KITOPS_SOURCES = src setup.py

#kusu kit-install package.
KIT_PKGS += PKG_KIT_INSTALL
PKG_KIT_INSTALL_SPEC = kusu-kit-install.spec
PKG_KIT_INSTALL_SOURCES = doc src/bin src/man src/lib

# Kusu Network Tool package.
KIT_PKGS += PKG_NETWORKTOOL
PKG_NETWORKTOOL_SPEC = kusu-networktool.spec
PKG_NETWORKTOOL_SOURCES = doc src/bin src/lib
#PKG_NETWORKTOOL_SOURCES = src setup.py

# Kusu UI package.
KIT_PKGS += PKG_UI
PKG_UI_SPEC = kusu-ui.spec
PKG_UI_SOURCES = doc src/bin src/lib
#PKG_UI_SOURCES = src setup.py

# Kusu Util package.
KIT_PKGS += PKG_UTIL
PKG_UTIL_SPEC = kusu-util.spec
PKG_UTIL_SOURCES = doc src/lib src/etc

# Initrd Templates package.
KIT_PKGS += PKG_INITRD_TEMPLATES
PKG_INITRD_TEMPLATES_SPEC = kusu-initrd-templates.spec
PKG_INITRD_TEMPLATES_SOURCES = etc overlay mkinitrd-templates

# Kusu Autoinstall package.
KIT_PKGS += PKG_AUTOINSTALL
PKG_AUTOINSTALL_SPEC = kusu-autoinstall.spec
PKG_AUTOINSTALL_SOURCES = src/doc src/lib src/etc

# Kusu Installer package.
KIT_PKGS += PKG_INSTALLER
PKG_INSTALLER_SPEC = kusu-installer.rhel.spec
PKG_INSTALLER_SOURCES = src/doc src/bin src/etc src/lib src/po

# Kusu Node Installer package.
KIT_PKGS += PKG_NODEINSTALLER
PKG_NODEINSTALLER_SPEC = kusu-nodeinstaller.spec
PKG_NODEINSTALLER_SOURCES = src/bin src/lib

# Kusu Node Installer Patchfiles package.
KIT_PKGS += PKG_NODEINSTALLER_PATCHFILES
PKG_NODEINSTALLER_PATCHFILES_SPEC = kusu-nodeinstaller-patchfiles.spec
PKG_NODEINSTALLER_PATCHFILES_SOURCES = src sbin bin man lib

# Kusu Node Installer Patchfiles package.
KIT_PKGS += PKG_RELEASE
PKG_RELEASE_SPEC = kusu-release.spec
PKG_RELEASE_SOURCES = src

# Kusu power management framework package.
KIT_PKGS += PKG_POWER
PKG_POWER_SPEC = kusu-power.spec
PKG_POWER_SOURCES = doc src setup.py

#3rd party packages

# Kusu Createrepo package.
KIT_PKGS += PKG_CREATEREPO
PKG_CREATEREPO_SPEC = kusu-createrepo.spec
PKG_CREATEREPO_SOURCES = custom src

# Kusu MD5 crypt package.
KIT_PKGS += PKG_MD5CRYPT
PKG_MD5CRYPT_SPEC = kusu-md5crypt.spec
PKG_MD5CRYPT_SOURCES = src

# Kusu Shell package.
KIT_PKGS += PKG_SHELL
PKG_SHELL_SPEC = kusu-shell.spec
PKG_SHELL_SOURCES = src/lib src/plugins src/bin src/man

# Kusu UAT package.
KIT_PKGS += PKG_UAT
PKG_UAT_SPEC = kusu-uat.spec
PKG_UAT_SOURCES = src/lib src/plugins src/etc

# Kusu Thttpd package.
KIT_PKGS += PKG_THTTPD
PKG_THTTPD_NAME = thttpd
PKG_THTTPD_VERSION = 2.25b
PKG_THTTPD_RELEASE = 16.fc9
PKG_THTTPD_ARCH = $(ARCH)
PKG_THTTPD_RPM = $(PKG_THTTPD_NAME)-$(PKG_THTTPD_VERSION)-$(PKG_THTTPD_RELEASE).$(PKG_THTTPD_ARCH).rpm

# Cheetah package.
KIT_PKGS += PKG_CHEETAH
PKG_CHEETAH_NAME = python-cheetah
PKG_CHEETAH_VERSION = 2.0.1
PKG_CHEETAH_RELEASE = 1.el5
PKG_CHEETAH_ARCH = $(ARCH)
PKG_CHEETAH_RPM = $(PKG_CHEETAH_NAME)-$(PKG_CHEETAH_VERSION)-$(PKG_CHEETAH_RELEASE).$(PKG_CHEETAH_ARCH).rpm

# Kusu Ipy package.
KIT_PKGS += PKG_IPY
PKG_IPY_NAME = python-IPy
PKG_IPY_VERSION = 0.60
PKG_IPY_RELEASE = 1.el5
PKG_IPY_ARCH = noarch
PKG_IPY_RPM = $(PKG_IPY_NAME)-$(PKG_IPY_VERSION)-$(PKG_IPY_RELEASE).$(PKG_IPY_ARCH).rpm

# Primitive package.
KIT_PKGS += PKG_PRIMITIVE
PKG_PRIMITIVE_NAME = kusu-primitive
PKG_PRIMITIVE_SPEC = kusu-primitive.spec
PKG_PRIMITIVE_SOURCES = config.mk Makefile src

# Kusu Path package.
KIT_PKGS += PKG_PATH
PKG_PATH_SPEC = kusu-path.spec
PKG_PATH_SOURCES = src

# Net tool package
KIT_PKGS += PKG_KUSU_NET_TOOL
PKG_KUSU_NET_TOOL_SPEC = kusu-net-tool.spec
PKG_KUSU_NET_TOOL_SOURCES = doc sbin man

# License support tool package
KIT_PKGS += PKG_KUSU_LICENSE_TOOL
PKG_KUSU_LICENSE_TOOL_SPEC = kusu-license-tool.spec
PKG_KUSU_LICENSE_TOOL_SOURCES = src/sbin src/man src/lib src/firstboot

# Python SQLite 2 package.
KIT_PKGS += PKG_PYSQLITE
PKG_PYSQLITE_NAME = python-sqlite2
PKG_PYSQLITE_VERSION = 2.3.3
PKG_PYSQLITE_RELEASE = 1.el5
PKG_PYSQLITE_ARCH = $(ARCH)
PKG_PYSQLITE_RPM = $(PKG_PYSQLITE_NAME)-$(PKG_PYSQLITE_VERSION)-$(PKG_PYSQLITE_RELEASE).$(PKG_PYSQLITE_ARCH).rpm

# Python SQL Alchemy package.
KIT_PKGS += PKG_SQLALCHEMY
PKG_SQLALCHEMY_NAME = python-sqlalchemy
PKG_SQLALCHEMY_VERSION = 0.3.11
PKG_SQLALCHEMY_RELEASE = 1.el5
PKG_SQLALCHEMY_ARCH = noarch
PKG_SQLALCHEMY_RPM = $(PKG_SQLALCHEMY_NAME)-$(PKG_SQLALCHEMY_VERSION)-$(PKG_SQLALCHEMY_RELEASE).$(PKG_SQLALCHEMY_ARCH).rpm

# Python Psycopg2  package.
KIT_PKGS += PKG_PSYCOPG2
PKG_PSYCOPG2_NAME = python-psycopg2
PKG_PSYCOPG2_VERSION = 2.0.7
PKG_PSYCOPG2_RELEASE = 1.el5
PKG_PSYCOPG2_ARCH = $(ARCH)
PKG_PSYCOPG2_RPM = $(PKG_PSYCOPG2_NAME)-$(PKG_PSYCOPG2_VERSION)-$(PKG_PSYCOPG2_RELEASE).$(PKG_PSYCOPG2_ARCH).rpm

# Modules package.
KIT_PKGS += PKG_MODULES
PKG_MODULES_NAME = environment-modules
PKG_MODULES_VERSION = 3.2.6
PKG_MODULES_RELEASE = 4.el5
PKG_MODULES_ARCH = $(ARCH)
PKG_MODULES_RPM = $(PKG_MODULES_NAME)-$(PKG_MODULES_VERSION)-$(PKG_MODULES_RELEASE).$(PKG_MODULES_ARCH).rpm

# PDSH package.
KIT_PKGS += PKG_PDSH
PKG_PDSH_NAME = pdsh
PKG_PDSH_VERSION = 2.14
PKG_PDSH_RELEASE = 2
PKG_PDSH_ARCH = $(ARCH)
PKG_PDSH_SRPM = $(PKG_PDSH_NAME)-$(PKG_PDSH_VERSION)-$(PKG_PDSH_RELEASE).src.rpm

# The PDSH RCMD EXEC is packaged separately.
# Version and release inerited from parent.
KIT_PKGS += PKG_PDSH_RCMD_EXEC
PKG_PDSH_RCMD_EXEC_NAME = pdsh-rcmd-exec
PKG_PDSH_RCMD_EXEC_PARENT = PKG_PDSH

# The PDSH RCMD SSH is packaged separately.
# Version and release inerited from parent.
KIT_PKGS += PKG_PDSH_RCMD_SSH
PKG_PDSH_RCMD_SSH_NAME = pdsh-rcmd-ssh
PKG_PDSH_RCMD_SSH_PARENT = PKG_PDSH

# The PDSH RCMD RSH is packaged separately.
# Version and release inerited from parent.
KIT_PKGS += PKG_PDSH_RCMD_RSH
PKG_PDSH_RCMD_RSH_NAME = pdsh-rcmd-rsh
PKG_PDSH_RCMD_RSH_PARENT = PKG_PDSH

# The PDSH MOD NETGROUP is packaged separately.
# Version and release inerited from parent.
KIT_PKGS += PKG_PDSH_MOD_NETGROUP
PKG_PDSH_MOD_NETGROUP_NAME = pdsh-mod-netgroup
PKG_PDSH_MOD_NETGROUP_PARENT = PKG_PDSH

# The PDSH MOD DSHGROUP is packaged separately.
# Version and release inerited from parent.
KIT_PKGS += PKG_PDSH_MOD_DSHGROUP
PKG_PDSH_MOD_DSHGROUP_NAME = pdsh-mod-dshgroup
PKG_PDSH_MOD_DSHGROUP_PARENT = PKG_PDSH

# The PDSH MOD MACHINES is packaged separately.
# Version and release inerited from parent.
KIT_PKGS += PKG_PDSH_MOD_MACHINES
PKG_PDSH_MOD_MACHINES_NAME = pdsh-mod-machines
PKG_PDSH_MOD_MACHINES_PARENT = PKG_PDSH

# inst-source-utils pkg
KIT_PKGS += PKG_INST_SOURCE_UTILS
PKG_INST_SOURCE_UTILS_NAME = inst-source-utils
PKG_INST_SOURCE_UTILS_VERSION = 2008.11.24
PKG_INST_SOURCE_UTILS_RELEASE = 2.1
PKG_INST_SOURCE_UTILS_ARCH = noarch
PKG_INST_SOURCE_UTILS_SRPM = $(PKG_INST_SOURCE_UTILS_NAME)-$(PKG_INST_SOURCE_UTILS_VERSION)-$(PKG_INST_SOURCE_UTILS_RELEASE).src.rpm
#PKG_INST_SOURCE_UTILS_SRPM_URL = http://fserv/engineering/build/sles/10/SRPMS/$(PKG_INST_SOURCE_UTILS_SRPM)

# Kusu Appglobals Tool package.
KIT_PKGS += PKG_KUSU_APPGLOBALS_TOOL
PKG_KUSU_APPGLOBALS_TOOL_SPEC = kusu-appglobals-tool.spec
PKG_KUSU_APPGLOBALS_TOOL_SOURCES = src/sbin src/lib src/man

# Kusu Setup package.
KIT_PKGS += PKG_SETUP
PKG_SETUP_NAME = kusu-setup
PKG_SETUP_SPEC = kusu-setup.spec
PKG_SETUP_SOURCES = ../kusu-nodeinstaller-patchfiles ../kusu-primitive/config.mk ../kusu-primitive/Makefile ../kusu-primitive/src ../kusu-util ../kusu-path ../kusu-buildkit ../kusu-kitops ../kusu-repoman ../kusu-core ../kusu-boot ../kusu-base-node src/bin src/lib doc ../../RPMS/noarch/python-IPy-0.60-1.el5.noarch.rpm ../../RPMS/noarch/python-sqlalchemy-0.3.11-1.el5.noarch.rpm ../../RPMS/x86_64/python-cheetah-2.0.1-2.2.x86_64.rpm ../../RPMS/x86_64/python-sqlite2-2.4.1-3.1.x86_64.rpm ../kusu-createrepo

