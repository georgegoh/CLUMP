# $Id: Makefile 3979 2008-12-22 11:35:16Z ltsai $
include ../../../config.mk

app_name = updatetool
executables = $(notdir $(basename $(wildcard bin/*)))

.PHONY: buildout
buildout: lib test
	echo $(executables)
	@mkdir -p $(UC_BUILDOUT_PATH)/$(UC_PYTHONAPP_PATH) $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(app_name) $(UC_BUILDOUT_PATH)/$(UC_PYTHONDIR)/test $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/app
	@touch $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/__init__.py
	@touch $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(module_name)/__init__.py
	@touch $(UC_BUILDOUT_PATH)/$(UC_PYTHONAPP_PATH)/__init__.py
	@echo "import pkgutil" > $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/app/__init__.py
	@echo "__path__ = pkgutil.extend_path(__path__, __name__)" >> $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/app/__init__.py
	(cd lib; find * | cpio -mpdu $(UC_BUILDOUT_PATH)/$(UC_PYTHONPATH)/$(app_name))
	(cd test; find * | cpio -mpdu $(UC_BUILDOUT_PATH)/$(UC_PYTHONDIR)/test)
	@rm -f $(UC_BUILDOUT_PATH)/$(UC_PYTHONAPP_PATH)/__init__
