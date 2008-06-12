# Copyright (C) 2007 Platform Computing Inc.
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
# $Id$
# 


# Be sure to change the MODULE and VERSION to fit your needs
MODULE = path
VERSION = 0.9


# The following settings can be changed accordingly to your needs
RELEASE = 0
NAME = kusu-$(MODULE)


# Please do not modify anything beyond this line unless you know what you
# are doing

KUSUROOT = /opt/kusu
ROOT = 


SPECFILES = `find . -maxdepth 1 -type f -name "*.spec"`
TOPDIR = $(PWD)/../..
KUSUSRC = $(TOPDIR)/../../..
KUSU_BUILD_MODULES_BIN = $(KUSUSRC)/bin/build-kusu-artefacts



rpm: install
	-mkdir -p $(TOPDIR)/BUILD/$(NAME)-$(VERSION)-$(RELEASE)
	@echo "Tarring $(NAME)"
	tar cf - . |(cd $(TOPDIR)/BUILD/$(NAME)-$(VERSION)-$(RELEASE) ; tar xf - )
	@if [ -f $(HOME)/.rpmmacros ] ; then \
		mv $(HOME)/.rpmmacros $(HOME)/.rpmmacros.OFF ; \
	fi
	echo "%_topdir $(TOPDIR)" > $(HOME)/.rpmmacros
	echo "%__os_install_post    \
	    /usr/lib/rpm/brp-compress \
	    %{!?__debug_package:/usr/lib/rpm/brp-strip %{__strip}} \
	    /usr/lib/rpm/brp-strip-static-archive %{__strip} \
	    /usr/lib/rpm/brp-strip-comment-note %{__strip} %{__objdump} \
	    /usr/lib/rpm/brp-java-repack-jars \
	%{nil}" >> $(HOME)/.rpmmacros
	for i in $(SPECFILES) ; do \
		(rpmbuild -bb $$i ) ;\
	done
	# @rm -rf $(HOME)/.rpmmacros



install::
	$(KUSU_BUILD_MODULES_BIN) build kususrc=$(KUSUSRC) modules=$(MODULE)
	sed \
		-e 's%@KUSUROOT@%$(KUSUROOT)%g' \
		-e 's%@NAME@%$(NAME)%g' \
	     	-e 's%@VERSION@%$(VERSION)%g' \
		-e 's%@RELEASE@%$(RELEASE)%g' \
		spec.tmpl > $(NAME).spec

clean::
	-@rm -rf bin etc info lib man share *.spec
	-@rm -rf $(TOPDIR)/BUILD/$(NAME)-$(VERSION)-$(RELEASE)
