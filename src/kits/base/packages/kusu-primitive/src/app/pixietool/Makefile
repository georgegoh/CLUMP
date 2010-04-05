# $Id: Makefile 3388 2008-09-01 05:39:58Z hirwan $
include ../../../config.mk

app_name = pixietool
executables = $(notdir $(basename $(wildcard bin/*)))

.PHONY: buildout
buildout:   bin lib test
	@mkdir -p $(UC_BUILDOUT_PATH)/$(UC_PYTHONAPP_PATH) $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(app_name) $(UC_BUILDOUT_PATH)/$(UC_PYTHONDIR)/test
	(cd bin; $(foreach exe, $(executables), install -m755 $(exe).py $(UC_BUILDOUT_PATH)/$(UC_PYTHONAPP_PATH)/$(exe);))
	(cd lib; find * | cpio -mpdu $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(app_name))
	(cd test; find * | cpio -mpdu $(UC_BUILDOUT_PATH)/$(UC_PYTHONDIR)/test)
