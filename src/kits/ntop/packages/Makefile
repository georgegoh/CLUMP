# Copyright (C) 2007 Platform Computing Corporation
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


TOPDIR = $(PWD)/..
ARCH=$(shell arch)

SRCDIRS = `find . -maxdepth 1 -type d -not -name .svn -not -name CVS \
	    -not -name .`

define check_prequisites
	echo "******************************************************************************"
        echo "rrdtool needs the following packages to build"
        echo ""
        echo "  openssl-devel"
        echo "  cgilib-devel (Built from this kit)"
        echo "  libart_lgpl-devel"
        echo "  libpng-devel"
        echo "  freetype-devel"
        echo "  ruby-devel"
        echo "  tk-devel"
        echo ""
        echo "ntop needs the following packages to build"
        echo ""
        echo "  openssl-devel"
        echo "  gdbm-devel"
        echo "  rrdtool-devel (Built from this kit)"
        echo "  glib-devel"
        echo "  gd-devel"
        echo "  automake"
        echo "  autoconf"
        echo "  libpcap-devel"
 	echo "  libtool"
	echo ""
	echo "******************************************************************************"
endef

define setrpmmacro
        if [ -f $(HOME)/.rpmmacros ] ; then \
                mv $(HOME)/.rpmmacros $(HOME)/.rpmmacros.OFF ; \
        fi
        echo "%_topdir $(TOPDIR)" > $(HOME)/.rpmmacros
endef

default: rpm

rpm:
	@$(call check_prequisites)
	@$(call setrpmmacro)

	@echo "Building Ntop..."
	rpmbuild --rebuild cgilib-0.5-1.src.rpm
	rpmbuild --rebuild rrdtool-1.2.23-1.src.rpm --define "_prefix /opt/ntop"
	rpmbuild --rebuild ntop-3.3-1.src.rpm  --define "dist el5" --define "_prefix /opt/ntop" --define "_initrddir /etc/init.d" --define "_sysconfdir /etc"
clean:
