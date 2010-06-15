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
# $Id: Makefile 2735 2007-11-14 06:33:23Z hirwan $
#
include config.mk

KITS_SRC_DIR=src/kits
INSTALLER_SRC_DIR=src/installer
EXTERNAL_PACKAGE_DIR=src/3rdparty

all:	iso srpms

init:
	@mkdir -p iso;

srpms:	init
	@for kit in $(KUSU_KITS_LISTS) ; do \
		echo "" ; \
		echo "====================================================================" ; \
		echo "Building kit srpms:  $$kit" ; \
		date ; \
		echo "====================================================================" ; \
		( cd $(KITS_SRC_DIR)/$$kit; $(MAKE) srpms ); \
	done

rpms:	init
	@for kit in $(KUSU_KITS_LISTS) ; do \
		echo "" ; \
		echo "====================================================================" ; \
		echo "Building kit rpms:  $$kit" ; \
		date ; \
		echo "====================================================================" ; \
		( cd $(KITS_SRC_DIR)/$$kit; $(MAKE) rpms); \
	done

iso:	init	
	-@rm -rf iso/*.iso
	@for kit in $(KUSU_KITS_LISTS) ; do \
		echo "" ; \
		echo "====================================================================" ; \
		echo "Building kit iso:  $$kit" ; \
		date ; \
		echo "====================================================================" ; \
		(cd $(KITS_SRC_DIR)/$$kit; $(MAKE) iso ); \
		find $(PWD)/$(KITS_SRC_DIR)/$$kit -type f -name '*.iso' -exec ln -sf {} iso/. \; ; \
	done

bootable-iso: init updatesimg
	@echo "====================================================================" ;
	@echo "Building:  bootable iso" ;
	@date ;
	@echo "Building for $(KUSU_DISTRO_NAME).$(KUSU_DISTRO_VERSION).$(KUSU_DISTRO_ARCH)" ;
	-@ls $(KUSU_DISTRO_SRC) >/dev/null
	-@ls $(KUSU_DISTRO_SRC) >/dev/null
	-@ls $(KUSU_DISTRO_SRC) >/dev/null
	@echo "Looking for distribution sources in $(KUSU_DISTRO_SRC)" ;
	@if [ -n "$(kitsource)" ]; then \
		echo "Kit source dir: $(kitsource) is specified. Using this for custom kernel/initrd instead of the distribution's kernel/initrd.'"; \
		bin/mk-bootable -d $(KUSU_DISTRO_NAME) \
			-v $(KUSU_DISTRO_VERSION) \
			-a $(KUSU_DISTRO_ARCH) \
			-s $(KUSU_DISTRO_SRC) \
			-k $(kitsource); \
	else \
		bin/mk-bootable -d $(KUSU_DISTRO_NAME) \
			-v $(KUSU_DISTRO_VERSION) \
			-a $(KUSU_DISTRO_ARCH) \
			-s $(KUSU_DISTRO_SRC); \
	fi;
	@echo "====================================================================" ;
	
	

updatesimg: init
	@if [ ! -f iso/kit-base-*.iso ]; then \
		echo "Please rebuild the Base kit!"; \
		exit -1; \
	fi; \
	echo "====================================================================" ; \
	echo "Building:  updates.img" ; \
	date ; \
	echo "====================================================================" ;\
	bin/gen-updatesimg ;
	@if [ -f ./updates.img ]; then \
		echo "Generated updates.img"; \
	fi; 
	

clean:
	@echo "====================================================================" ;
	@echo "Cleaning:  removing build artifacts" ;
	@date ;
	@echo "====================================================================" ;
	@for kit in $(KUSU_KITS_LISTS) ; do ( cd $(KITS_SRC_DIR)/$$kit && make clean ) ; done
	@rm -rf rpm iso;
	@rm -f *.iso
	@rm -f updates.img
