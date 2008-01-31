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
#
# NOTE:  The packaging is GPL, but LSF is not.
#
# $Id$
#

NAME = lsf
VERSION = 7.0.2
RELEASE = 0
TOPDIR = $(PWD)
ARCH = $(shell arch)
RPMS = `find $(TOPDIR)/RPMS/ -type f |grep -v '.svn'`

DOCPATH=/pcc/id_trusted/publish/lsf/7.0.2
DOCFILE=lsf7Update2_documentation.tar.Z

default: all
all:	packages components kit

packages:
	-mkdir -p $(TOPDIR)/RPMS/$(ARCH)
	cd packages; make

components:
	cd components; make

kit:
	@if [ -f $(HOME)/.rpmmacros ] ; then \
		mv $(HOME)/.rpmmacros $(HOME)/.rpmmacros.OFF ; \
	fi
	-mkdir -p $(TOPDIR)/BUILD
	-mkdir -p $(TOPDIR)/RPMS/noarch
	echo "%_topdir $(TOPDIR)" > $(HOME)/.rpmmacros
	rm -rf docs/files/*
	mkdir -p docs/files
	# Wakeup automounter.  Needed for PCC NFS dirs
	-ls -l $(DOCPATH)/$(DOCFILE)
	@sleep 1
	@if [ -f $(DOCPATH)/$(DOCFILE) ] ; then \
		cp $(DOCPATH)/$(DOCFILE) docs/files ; \
		cd docs/files ; tar zxf $(DOCFILE) ; \
		cd $(VERSION) ; mv * .. ; \
		cd .. ; rm -rf $(VERSION) ; \
	else \
		echo "ERROR NO DOCUMENTATION FOUND!" ; \
		exit -1 ; \
	fi
	rpmbuild -bb kit-$(NAME).spec
	-rm -rf $(HOME)/.rpmmacros
	mkdir -p $(TOPDIR)/disk1/$(NAME)
	cd $(TOPDIR)/disk1/$(NAME) ; \
	for i in $(RPMS); do ln -fs $$i; done 
	mkisofs -quiet -V "LSF $(VERSION) Kit" -r -T -f -o kit-$(NAME)-$(VERSION)-$(RELEASE).x86_64.iso disk1

clean:
	rm -rf $(TOPDIR)/RPMS/$(ARCH)/*
	rm -rf $(TOPDIR)/disk1
	cd components; make clean
	cd packages; make clean
	rm -rf docs/files
	rm -rf kit-*.iso BUILD RPMS SOURCES
	rm -rf *.rpm
	rm -rf templates

.PHONY: components packages 
