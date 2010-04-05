# $Id: Makefile 3352 2008-08-27 09:02:31Z hirwan $
include ../../../config.mk

module_name = core

.PHONY: buildout
buildout:	lib test
	@mkdir -p $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(module_name) $(UC_PYTHONDIR)/test
	@touch $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/__init__.py
	@touch $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(module_name)/__init__.py
	(cd lib; find * | cpio -mpdu $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(module_name))
	(cd test; find * | cpio -mpdu $(UC_BUILDOUT_PATH)/$(UC_PYTHONDIR)/test)
