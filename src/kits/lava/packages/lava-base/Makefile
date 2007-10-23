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
# $Id$
# 


RELEASE = 1
ROOT = 
NAME = lava
VERSION = 1.0
BINARY_ARCH=linux2.6-glibc2.3-x86
DOWNLOAD_SITE = http://www.osgdc.org/pub/build/kits/lava


# Default cluster name
CLUSTER_NAME = lava

SPECFILES = `find . -maxdepth 1 -type f -name "*.spec"`
TOPDIR = $(PWD)/../..
ARCH=$(shell arch)

rpm:
	-mkdir -p $(TOPDIR)/BUILD
	-mkdir -p $(TOPDIR)/SOURCES
	-mkdir -p $(TOPDIR)/RPMS/$(ARCH)

	# Copy the tarballs from PCC if available and put into kit automatically.
	-cp /pcc/lsf_madison/Lava/$(VERSION)/lava$(VERSION)_linux2.6-glibc2.3-x86.tar.Z $(TOPDIR)/BUILD

	# If not available, download the tarballs from the DOWNLOAD_SITE and put into kit automatically.
	if [ ! -f $(TOPDIR)/BUILD/lava$(VERSION)_linux2.6-glibc2.3-x86.tar.Z ] ; then \
		if [ "x${ARCH}" == "xx86_64" ] ; then \
		    echo "*** Copying Fake 64bit Lava..."; \
		    curl -o $(TOPDIR)/BUILD/lava$(VERSION)_linux2.6-glibc2.3-x86.tar.Z -L $(DOWNLOAD_SITE)/lava$(VERSION)_linux2.6-glibc2.3-x86.tar.Z ; \
		elif [ "x${ARCH}" == "xi386" -o "x${ARCH}" == "xi686" ] ; then \
		    curl -o $(TOPDIR)/BUILD/lava$(VERSION)_linux2.6-glibc2.3-x86.tar.Z -L $(DOWNLOAD_SITE)/lava$(VERSION)_linux2.6-glibc2.3-x86.tar.Z $(TOPDIR)/BUILD ; \
		fi \
	fi

	@echo "Tarring $(NAME)"
	tar cf - . |(cd $(TOPDIR)/BUILD/ ; tar xf - )
	@if [ -f $(HOME)/.rpmmacros ] ; then \
		mv $(HOME)/.rpmmacros $(HOME)/.rpmmacros.OFF ; \
	fi
	echo "%_topdir $(TOPDIR)" > $(HOME)/.rpmmacros
	for i in $(SPECFILES) ; do \
		(rpmbuild -bb $$i ) ;\
	done
	# @rm -rf $(HOME)/.rpmmacros

install::
