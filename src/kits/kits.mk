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

# Setting some defaults.
KIT_TOPDIR = $(PWD)
ARTIFACT_DIR = artifacts
KIT_ARTIFACT_DIR = $(ARTIFACT_DIR)/$(KIT_NAME)
ARCH = $(shell uname -i)

ifndef KIT_TOPDIR
RPMBUILD=rpmbuild
else
RPMBUILD=rpmbuild --define "_topdir $(KIT_TOPDIR)" --define "debug_package %{nil}"
endif

SOURCEDIR = SOURCES
SPECDIR = SPECS
SRPMDIR = SRPMS
RPMDIR = RPMS

PACKAGESDIR = packages
TMPDIR = /tmp

# Command options passed to mkisofs.
MKISOFS_OPTS = -r -T -f -quiet

# Python variables
PYTHON_VERSION = $(shell python -c 'import sys ; print sys.version[:3]')
PYTHON_SITELIB = $(shell python -c 'from distutils.sysconfig import get_python_lib; print get_python_lib()')

# Derived variables.
KIT_NAME_VER = $(KIT_NAME)-$(KIT_VERSION)-$(KIT_RELEASE)
KIT_NAME_VER_ARCH = $(KIT_NAME_VER).$(KIT_ARCH)
KIT_SRPM_FILENAME = kit-$(KIT_NAME_VER).src.rpm
KIT_RPM_FILENAME = kit-$(KIT_NAME_VER_ARCH).rpm
KIT_ISO_FILENAME = kit-$(KIT_NAME_VER_ARCH).iso

# Escape forward slashes as that's the delimiter used in the sed command.
KIT_PROPER_NAME_ESC=$(subst /,\/,$(KIT_PROPER_NAME))
KIT_NAME_ESC=$(subst /,\/,$(KIT_NAME))
KIT_VERSION_ESC=$(subst /,\/,$(KIT_VERSION))
KIT_RELEASE_ESC=$(subst /,\/,$(KIT_RELEASE))
KIT_ARCH_ESC=$(subst /,\/,$(KIT_ARCH))

# Helper "functions".
PKG_SPEC_NAME = $(if $($(1)_SPEC),$($(1)_SPEC),$($(1)_NAME)-$($(1)_VERSION).spec)
PKG_PREFIX_SPEC_NAME = $(SPECDIR)/$(call PKG_SPEC_NAME,$(1))
PKG_SRPM_NAME = $(if $($(1)_SRPM),$($(1)_SRPM),$($(1)_NAME)-$($(1)_VERSION)-$($(1)_RELEASE).src.rpm)
PKG_PREFIX_SRPM_NAME = $(SRPMDIR)/$(call PKG_SRPM_NAME,$(1))
PKG_RPM_NAME = $(if $($(1)_RPM),$($(1)_RPM),$($(1)_NAME)-$($(1)_VERSION)-$($(1)_RELEASE).$($(1)_ARCH).rpm)
PKG_PREFIX_RPM_NAME = $(if $(2),$(2),$(RPMDIR)/$($(1)_ARCH))/$(call PKG_RPM_NAME,$(1))
PKG_SUBRPM_NAME = $(if $($(1)_RPM),$($(1)_RPM),$($(1)_NAME)-$($($(1)_PARENT)_VERSION)-$($($(1)_PARENT)_RELEASE).$($($(1)_PARENT)_ARCH).rpm)
PKG_PREFIX_SUBRPM_NAME = $(if $(2),$(2),$(RPMDIR)/$($($(1)_PARENT)_ARCH))/$(call PKG_SUBRPM_NAME,$(1))

PKG_SOURCES = $(if $($(1)_SOURCES),$($(1)_SOURCES))
PKG_PREFIX_SRCDIR = $(PACKAGESDIR)/$($(1)_NAME)

# if "<pkg>_TARBALL_SUBVER" is defined, append it to the tarball filename
# else use _RELEASE instead.
PKG_PREFIX_TARBALL_NAME = $(SOURCEDIR)/$($(1)_NAME)-$($(1)_VERSION)$(if $($(1)_TARBALL_SUBVER),.$($(1)_TARBALL_SUBVER),.$($(1)_RELEASE)).tar.gz

PKG_RPMBUILD_OPTIONS = $(if $($(1)_RPMBUILD_OPTIONS),$($(1)_RPMBUILD_OPTIONS))

#get package from url
PKG_RPM_URL = $(if $($(1)_RPM_URL),$($(1)_RPM_URL))
define PKG_GET_RPM_FROM_URL
ifdef $(1)_RPM_URL
_$(1)_rpmurl_tgt = $(call PKG_PREFIX_RPM_NAME,$(1))
RPM_ARTIFACTS += $$(_$(1)_rpmurl_tgt)
$$(_$(1)_rpmurl_tgt):
	@echo running make $$(_$(1)_rpmurl_tgt)
	wget -nd --waitretry=60 --continue -O $(call PKG_PREFIX_RPM_NAME,$(1)) $(call PKG_RPM_URL,$(1))
endif
endef

PKG_SRPM_URL = $(if $($(1)_SRPM_URL),$($(1)_SRPM_URL))
define PKG_GET_SRPM_FROM_URL
ifdef $(1)_SRPM_URL
_$(1)_rpmurl_tgt = $(call PKG_PREFIX_SRPM_NAME,$(1))
RPM_ARTIFACTS += $$(_$(1)_rpmurl_tgt)
$$(_$(1)_rpmurl_tgt):
	@echo running make $$(_$(1)_rpmurl_tgt)
	wget -nd --waitretry=60 --continue -O $(call PKG_PREFIX_SRPM_NAME,$(1)) $(call PKG_SRPM_URL,$(1))
endif
endef

#_$(1)_tar_tgt = $(call PKG_PREFIX_SPEC_NAME,$(1))
#TGZ_ARTIFACTS += $(call PKG_PREFIX_TARBALL_NAME,$(1))
# cp -pf $(call PKG_PREFIX_SRCDIR,$(1))/$($(1)_NAME).spec $(SPECDIR)/.
define PACK_PKG_SRC_TARBALL
_$(1)_tar_tgt = $(call PKG_PREFIX_TARBALL_NAME,$(1))
_$(1)_TARBALL_FILENAME += $$(_$(1)_tar_tgt)
TGZ_ARTIFACTS += $$(_$(1)_tar_tgt)
$$(_$(1)_tar_tgt):	$(call PKG_PREFIX_SRCDIR,$(1))
	@echo running make $$(_$(1)_tar_tgt)
	mkdir -p $(TMPDIR)/$($(1)_NAME)-build/$($(1)_NAME)
	(cd $(call PKG_PREFIX_SRCDIR,$(1)) && rsync -a $(call PKG_SOURCES,$(1)) $(TMPDIR)/$($(1)_NAME)-build/$($(1)_NAME)/. --exclude .svn)
	(cd $(TMPDIR)/$($(1)_NAME)-build && tar czf $(KIT_TOPDIR)/$(call PKG_PREFIX_TARBALL_NAME,$(1)) $($(1)_NAME))
	rm -rf $(TMPDIR)/$($(1)_NAME)-build
endef

define PKG_GET_DATA_FROM_SPEC
ifndef $(1)_NAME
$(1)_NAME = $(shell grep ^Name: $(call PKG_PREFIX_SPEC_NAME,$(1)) | awk '{print $$2 }')
endif
ifndef $(1)_VERSION
$(1)_VERSION = $(shell grep ^Version: $(call PKG_PREFIX_SPEC_NAME,$(1)) | awk '{print $$2 }')
endif
ifndef $(1)_RELEASE
$(1)_RELEASE = $(shell grep ^Release: $(call PKG_PREFIX_SPEC_NAME,$(1)) | awk '{print $$2 }')
endif
ifndef $(1)_ARCH
$(1)_ARCH = $(shell grep ^BuildArch: $(call PKG_PREFIX_SPEC_NAME,$(1)) | awk '{print $$2 }')
endif
ifndef $(1)_ARCH
$(1)_ARCH = $(ARCH)
endif
endef

define PKG_SRPM_FROM_SPEC
_$(1)_srpm_tgt = $(call PKG_PREFIX_SRPM_NAME,$(1))
SRPM_ARTIFACTS += $$(_$(1)_srpm_tgt)
$$(_$(1)_srpm_tgt): $(call PKG_PREFIX_SPEC_NAME,$(1)) $(_$(1)_TARBALL_FILENAME)
	@echo running make $$(_$(1)_srpm_tgt)
	$(RPMBUILD) -bs $$(strip $$(word 1,$$^))
endef

define PKG_RPM_FROM_SPEC
_$(1)_rpmspec_tgt = $(call PKG_PREFIX_RPM_NAME,$(1))
RPM_ARTIFACTS += $$(_$(1)_rpmspec_tgt)
$$(_$(1)_rpmspec_tgt): $(call PKG_PREFIX_SPEC_NAME,$(1)) $(_$(1)_TARBALL_FILENAME)
	@echo running make $$(_$(1)_rpmspec_tgt)
	$(RPMBUILD) -bb $(call PKG_RPMBUILD_OPTIONS,$(1)) $$(strip $$(word 1,$$^))
endef

define PKG_RPM_FROM_SRPM
_$(1)_rpmsrpm_tgt = $(call PKG_PREFIX_RPM_NAME,$(1))
RPM_ARTIFACTS += $$(_$(1)_rpmsrpm_tgt)
$$(_$(1)_rpmsrpm_tgt): $(call PKG_PREFIX_SRPM_NAME,$(1))
	@echo running make $$(_$(1)_rpmsrpm_tgt)
	$(RPMBUILD) --rebuild $(call PKG_RPMBUILD_OPTIONS,$(1)) $$^
endef

define PKG_SUBRPM_FROM_PARENT
_$(1)_subrpm_tgt = $(call PKG_PREFIX_SUBRPM_NAME,$(1))
RPM_ARTIFACTS += $$(_$(1)_subrpm_tgt)
$$(_$(1)_subrpm_tgt): $(call PKG_PREFIX_RPM_NAME,$($(1)_PARENT))
	# $$@ is generated from $$^'s SRPM
endef

define PKG_ARTIFACT_FROM_RPM
_$(1)_iso_tgt = $(call PKG_PREFIX_RPM_NAME,$(1),$(KIT_ARTIFACT_DIR))
ISO_ARTIFACTS += $$(_$(1)_iso_tgt)
$$(_$(1)_iso_tgt): $(call PKG_PREFIX_RPM_NAME,$(1)) $(KIT_ARTIFACT_DIR)
	ln -sf ../../$$(strip $$(word 1,$$^)) $$@
endef

define PKG_ARTIFACT_FROM_SUBRPM
_$(1)_isosub_tgt = $(call PKG_PREFIX_SUBRPM_NAME,$(1),$(KIT_ARTIFACT_DIR))
ISO_ARTIFACTS += $$(_$(1)_isosub_tgt)
$$(_$(1)_isosub_tgt): $(call PKG_PREFIX_SUBRPM_NAME,$(1)) $(KIT_ARTIFACT_DIR)
	ln -sf ../../$$(strip $$(word 1,$$^)) $$@
endef

# Discover any spec file templates; only supported for kit/component RPMs.
KIT_PLUGINS = $(wildcard $(SOURCEDIR)/plugins/**/*)

# Determine how to process each package.
SOURCE_MODE_PKGS = $(strip $(foreach pkg,$(KIT_PKGS),$(if $($(pkg)_SOURCES),$(pkg))))
SOURCE_MODE_RULES = PACK_PKG_SRC_TARBALL
PARENT_MODE_PKGS = $(strip $(foreach pkg,$(KIT_PKGS),$(if $($(pkg)_PARENT),$(pkg))))
PARENT_MODE_RULES = PKG_ARTIFACT_FROM_SUBRPM PKG_SUBRPM_FROM_PARENT
SPEC_MODE_PKGS = $(strip $(foreach pkg,$(KIT_PKGS),$(if $($(pkg)_SPEC),$(pkg))))
SPEC_MODE_RULES = PKG_ARTIFACT_FROM_RPM PKG_RPM_FROM_SPEC PKG_SRPM_FROM_SPEC
SRPM_MODE_PKGS = $(strip $(foreach pkg,$(KIT_PKGS),$(if $($(pkg)_SRPM),$(pkg))))
SRPM_MODE_RULES = PKG_GET_SRPM_FROM_URL PKG_ARTIFACT_FROM_RPM PKG_RPM_FROM_SRPM
RPM_MODE_PKGS = $(strip $(foreach pkg,$(KIT_PKGS),$(if $($(pkg)_RPM),$(pkg))))
RPM_MODE_RULES = PKG_GET_RPM_FROM_URL PKG_ARTIFACT_FROM_RPM
INSTALLER_MODE_PKGS = $(strip $(foreach pkg,$(INSTALLER_MODE_PKGS),$(if $($(pkg)_RPM),$(pkg))))
INSTALLER_MODE_RULES = PKG_GET_RPM_FROM_URL

# The order of the targets is important here. The target `iso' is first,
# so it is chosen as the default target when `make' is run without targets
# on the command line. Targets generated from KIT_PKGS need to be defined
# before their variables (SRPM_ARTIFACTS, ISO_ARTIFACTS, etc) are used.

.PHONY: iso
iso: rpms $(KIT_ISO_FILENAME)

.PHONY: all
all: iso srpms

# First we need to generate any information we might need from a spec file.
$(foreach pkg,$(SPEC_MODE_PKGS),$(eval $(call PKG_GET_DATA_FROM_SPEC,$(pkg))))

# Generate targets for each package.
$(foreach pkg,$(SOURCE_MODE_PKGS),$(foreach rule,$(SOURCE_MODE_RULES),$(eval $(call $(rule),$(pkg)))))
$(foreach pkg,$(PARENT_MODE_PKGS),$(foreach rule,$(PARENT_MODE_RULES),$(eval $(call $(rule),$(pkg)))))
$(foreach pkg,$(SRPM_MODE_PKGS),$(foreach rule,$(SRPM_MODE_RULES),$(eval $(call $(rule),$(pkg)))))
$(foreach pkg,$(SPEC_MODE_PKGS),$(foreach rule,$(SPEC_MODE_RULES),$(eval $(call $(rule),$(pkg)))))
$(foreach pkg,$(RPM_MODE_PKGS),$(foreach rule,$(RPM_MODE_RULES),$(eval $(call $(rule),$(pkg)))))
$(foreach pkg,$(INSTALLER_PKGS),$(foreach rule,$(INSTALLER_MODE_RULES),$(eval $(call $(rule),$(pkg)))))

.PHONY: tgzs
tgzs: $(TGZ_ARTIFACTS)

.PHONY: specs
specs: $(SPEC_ARTIFACTS)

.PHONY: srpms
srpms: $(SRPM_ARTIFACTS)

.PHONY: rpms
rpms: $(RPM_ARTIFACTS)

.PHONY: artifacts
artifacts: $(ISO_ARTIFACTS)

$(KIT_ARTIFACT_DIR):
	mkdir -p $(KIT_ARTIFACT_DIR)

$(KIT_ISO_FILENAME): $(ISO_ARTIFACTS)
	mkisofs $(MKISOFS_OPTS) -V "$(KIT_PROPER_NAME) kit" -o $(KIT_ISO_FILENAME) $(ARTIFACT_DIR)

.PHONY: clean_iso
clean_iso:
	-rm -rf $(KIT_ISO_FILENAME)

.PHONY: clean_specs
clean_specs:
	-rm -rf $(SPEC_ARTIFACTS)

.PHONY: clean_srpms
clean_srpms:
	-rm -rf $(SRPM_ARTIFACTS)

.PHONY: clean_rpms
clean_rpms:
	-rm -rf $(RPM_ARTIFACTS)

.PHONY: clean_artifacts
clean_artifacts:
	-rm -rf $(ISO_ARTIFACTS) $(ARTIFACT_DIR) $(TGZ_ARTIFACTS)

.PHONY: clean
clean: clean_iso clean_specs clean_srpms clean_rpms clean_artifacts
	-rm -rf BUILD/*
