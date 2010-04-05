# $Id: Makefile 3394 2008-09-02 04:59:05Z ggoh $
include ../../../config.mk

module_name = autoinstall

.PHONY: buildout
buildout: lib
	@mkdir -p $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(module_name) $(UC_PYTHONDIR)/test
	@touch $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/__init__.py
	@touch $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(module_name)/__init__.py
	(cd lib; find * | cpio -mpdu $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(module_name))
