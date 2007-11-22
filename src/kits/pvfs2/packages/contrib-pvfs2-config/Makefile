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
        echo "pvfs2 needs the following packages to build"
        echo ""
        echo "  db4-devel"
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
#	@$(call setrpmmacro)

	@echo "Building PVFS2 kernel module..."
	-@mkdir $(TOPDIR)/../SRPMS -p
	-@mkdir $(TOPDIR)/../BUILD -p
	-@mkdir $(TOPDIR)/../RPMS/x86_64 -p
	cp $(TOPDIR)/../SRPMS/pvfs2-kernel-module*.src.rpm /usr/src/redhat/SRPMS
	rpmbuild -bs contrib-pvfs2-config.spec
	rpmbuild --rebuild $(TOPDIR)/../SRPMS/contrib-pvfs2-config-2.7.0-0.src.rpm
clean:
