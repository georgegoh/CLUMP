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
# $Id: Makefile 1357 2007-06-15 04:35:58Z hirwan $
# 

# The following settings can be changed accordingly to your needs
NAME = kusu-nodeinstaller-patchfiles
VERSION = 0.4
RELEASE = 0


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
	rm -f $(TOPDIR)/BUILD/$(NAME)-$(VERSION)-$(RELEASE)/spec.tmpl
	rm -f $(TOPDIR)/BUILD/$(NAME)-$(VERSION)-$(RELEASE)/$(NAME).spec
	rm -f $(TOPDIR)/BUILD/$(NAME)-$(VERSION)-$(RELEASE)/Makefile	
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
	sed \
		-e 's%@KUSUROOT@%$(KUSUROOT)%g' \
		-e 's%@NAME@%$(NAME)%g' \
	     	-e 's%@VERSION@%$(VERSION)%g' \
		-e 's%@RELEASE@%$(RELEASE)%g' \
		spec.tmpl > $(NAME).spec

clean::
	-@rm -rf *.spec centos fedora
	-@rm -rf $(TOPDIR)/BUILD/$(NAME)-$(VERSION)-$(RELEASE)
