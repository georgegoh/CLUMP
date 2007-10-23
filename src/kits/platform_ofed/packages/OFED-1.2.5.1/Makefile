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

TOPDIR = $(PWD)/../..
OFEDDIR=OFED-1.2.5.1
SRCNAME=OFED-1.2.5.1.tgz
SRCDIR=$(PWD)/
SRCFILE=$(SRCDIR)/$(SRCNAME)
TARARGS=zxf

define check_prequisites
	echo "--------------------------------------------------------"
	echo ""
	echo "Building this kit requires the folloowing prerequisites:"
	echo ""
	echo "   glibc-devel"
	echo "   gcc-c++"
	echo "   zlib-devel"
	echo "   pciutils-devel"
	echo "   tcl-devel"
	echo "   tk"
	echo "	 kernel-devel-2.6.18-8.el5"
	echo "--------------------------------------------------------"
endef



default:        rpm

rpm:	
	@$(call check_prequisites)
	@echo "Building OFED Packages (This will take a while...)"
	@if [ ! -d ${TOPDIR}/RPMS ]; then \
		mkdir -p ${TOPDIR}/RPMS ; \
	fi
	@if [ ! -f ${TOPDIR}/RPMS/kernel-ib-devel*.rpm ]; then \
		tar ${TARARGS} ${SRCFILE} ; \
		cp ofed.conf ${OFEDDIR} ; \
		cd ${OFEDDIR} ;./build.sh -c ofed.conf ; \
		cd ${OFEDDIR} ;mv -v RPMS/*/*.rpm ../../../RPMS ; \
	else \
		echo "Skipping build.  Packages exist" ; \
	fi

clean::
	@echo "Cleaning OFED Packages...."
	-@rm -rfv RPMS/* 
	@if [ -d ${OFEDDIR} ]; then \
		rm -rf ${OFEDDIR} ; \
	fi
