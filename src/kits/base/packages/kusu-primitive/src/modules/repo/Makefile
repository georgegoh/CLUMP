# $Id: Makefile 3378 2008-08-29 13:10:58Z ltsai $
include ../../../config.mk

module_name = repo

.PHONY: buildout
buildout:	lib test
	@mkdir -p $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(module_name) $(UC_PYTHONDIR)/test
	@touch $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/__init__.py
	@touch $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(module_name)/__init__.py
	(cd lib; find * | cpio -mpdu $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(module_name))
	(cd test; find * | cpio -mpdu $(UC_BUILDOUT_PATH)/$(UC_PYTHONDIR)/test)
