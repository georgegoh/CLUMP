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
# $Id$
#

NAME = base
VERSION = 0.1
RELEASE = 0
TOPDIR = $(PWD)
ARCH = $(shell arch)
RPMS = `find $(TOPDIR)/RPMS/ -type f |grep -v '.svn'`

default: all
all:	packages components kit

packages:
	cd packages; make

components:
	cd components; make

kit:
	if [ -f $(HOME)/.rpmmacros ] ; then \
		mv $(HOME)/.rpmmacros $(HOME)/.rpmmacros.OFF ; \
	fi
	-mkdir -p $(TOPDIR)/BUILD
	echo "%_topdir $(TOPDIR)" > $(HOME)/.rpmmacros
	rpmbuild -bb kit-$(NAME).spec
	-rm -rf $(HOME)/.rpmmacros
	mkdir -p $(TOPDIR)/disk1/$(NAME)
	cd $(TOPDIR)/disk1/$(NAME) ; \
	for i in $(RPMS); do ln -sf $$i; done 
	mkisofs -quiet -V "Base Kit" -r -T -f -o kit-$(NAME)-$(VERSION)-$(RELEASE).noarch.iso disk1

clean:
	cd $(TOPDIR)/RPMS ; rm -rf *
	rm -rf $(TOPDIR)/disk1
	cd components; make clean
	cd packages; make clean
	rm -rf kit-*.iso BUILD
	rm -rf *.rpm


.PHONY: components packages 
