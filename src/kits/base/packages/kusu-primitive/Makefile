# $Id: Makefile 3977 2008-12-22 09:23:47Z hirwan $
include config.mk

TOP_DIR = $(PWD)

ifndef TOP_DIR
RPMBUILD=rpmbuild
else
RPMBUILD=rpmbuild --define "_topdir $(TOP_DIR)" --define "debug_package %{nil} "
endif

MODULES = $(dir $(wildcard $(UC_MODULES_PATH)/*/Makefile))
APPS = $(dir $(wildcard $(UC_APPS_PATH)/*/Makefile))
3RDPARTY = $(dir $(wildcard $(UC_3RDPARTY_PATH)/*/Makefile))

all:	modules apps

nodeps:	modules apps

.PHONY: modules $(MODULES)
modules:	$(MODULES)
$(MODULES):
	@echo $@
	@$(MAKE) -C $@

.PHONY: apps $(APPS)
apps:	$(APPS)
$(APPS):
	@echo $@
	@$(MAKE) -C $@

.PHONY: 3rdparty $(3RDPARTY)
3rdparty:	$(3RDPARTY)
$(3RDPARTY):
	@echo $@
	@$(MAKE) -C $@

.PHONY: ucprofile
ucprofile:
	@mkdir -p $(UC_BUILDOUT_PATH)/bin
	@echo "#!/bin/bash" > $(UC_BUILDOUT_PATH)/bin/ucprofile.sh
	@echo "export PATH=$(UC_BUILDOUT_PATH)/bin:$(UC_BUILDOUT_PATH)/sbin:$(UC_BUILDOUT_PATH)/$(UC_LIBEXEC_PATH):\$$PATH" > $(UC_BUILDOUT_PATH)/bin/ucprofile.sh
	@echo "export LD_LIBRARY_PATH=$(UC_BUILDOUT_PATH)/lib:\$$LD_LIBRARY_PATH" >> $(UC_BUILDOUT_PATH)/bin/ucprofile.sh
	@echo "export UC_LIB_PATH="$(UC_BUILDOUT_PATH)/$(UC_LIBEXEC_PATH) >> $(UC_BUILDOUT_PATH)/bin/ucprofile.sh
	@echo "export PYTHONPATH="$(UC_BUILDOUT_PATH)/lib/python$(PYTHON_VERSION)/site-packages:$(UC_BUILDOUT_PATH)/lib64/python$(PYTHON_VERSION)/site-packages:$(UC_BUILDOUT_PATH)/$(UC_PYTHONDIR)/site-packages:$(UC_BUILDOUT_PATH)/$(UC_LIBEXEC_PATH) >> $(UC_BUILDOUT_PATH)/bin/ucprofile.sh
	@chmod 755 $(UC_BUILDOUT_PATH)/bin/ucprofile.sh

test:	3rdparty modules apps ucprofile
	(. $(UC_BUILDOUT_PATH)/bin/ucprofile.sh; nosetests -v --with-nosexunit --core-target=target/xml-report buildout/primitive/lib/python2.4/test)

$(TOP_DIR)/SOURCES/$(UC_NAME)-$(UC_VERSION).tar.bz2:	config.mk Makefile src
	@mkdir -p $(TOP_DIR)/SOURCES/$(UC_NAME)
	find config.mk | cpio -mpdu $(TOP_DIR)/SOURCES/$(UC_NAME)/.
	find Makefile | cpio -mpdu $(TOP_DIR)/SOURCES/$(UC_NAME)/.
	find src | cpio -mpdu $(TOP_DIR)/SOURCES/$(UC_NAME)/.
	(cd $(TOP_DIR)/SOURCES; tar -cjf $(TOP_DIR)/SOURCES/$(UC_NAME)-$(UC_VERSION).tar.bz2 $(UC_NAME))
	@rm -rf $(TOP_DIR)/SOURCES/$(UC_NAME)

rpm:	$(TOP_DIR)/SOURCES/$(UC_NAME)-$(UC_VERSION).tar.bz2 $(TOP_DIR)/SPECS/primitive.spec
	$(RPMBUILD) -ba $(TOP_DIR)/SPECS/primitive.spec

	
