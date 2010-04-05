# $Id: Makefile 3418 2008-09-12 12:55:35Z hsaliak $
include ../../../config.mk

app_name = configtool
executables = $(notdir $(basename $(wildcard bin/*)))

.PHONY: buildout
buildout: lib test
	@mkdir -p $(UC_BUILDOUT_PATH)/$(UC_PYTHONAPP_PATH) $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(app_name) $(UC_BUILDOUT_PATH)/$(UC_PYTHONDIR)/test
	(cd lib; find * | cpio -mpdu $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(app_name))
	(cd test; find * | cpio -mpdu $(UC_BUILDOUT_PATH)/$(UC_PYTHONDIR)/test)
