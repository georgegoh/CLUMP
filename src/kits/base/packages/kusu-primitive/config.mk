# $Id$
UC_NAME = primitive
UC_VERSION = 0.5
UC_RELEASE = 1
UC_MODULES_PATH = src/modules
UC_APPS_PATH = src/app
UC_3RDPARTY_PATH = src/3rdparty

UC_BUILDOUT_PATH = $(PWD)/buildout

UC_LIBEXEC_PATH = primitive/libexec
UC_LIB_PATH = primitive/lib

PYTHON_VERSION = $(shell python -c 'import sys; print sys.version[:3]')
UC_PYTHONDIR = $(UC_LIB_PATH)/python$(PYTHON_VERSION)
UC_PYTHONPATH = $(UC_PYTHONDIR)/site-packages/primitive
UC_PYTHONAPP_PATH = $(UC_LIBEXEC_PATH)
