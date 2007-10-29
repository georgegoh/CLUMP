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
NAME = lsf
VERSION = 7.0
BINARY_ARCH=linux2.6-glibc2.3-x86

SPECFILES = `find . -maxdepth 1 -type f -name "*.spec"`
TOPDIR = $(PWD)/../..
ARCH=$(shell arch)
export CLUSTERNAME=$(shell grep XXX_lsfmc_XXX /etc/hosts | sed -e "s/^[ \t]*\#.*//g")

rpm:
	-mkdir -p $(TOPDIR)/BUILD
	-mkdir -p $(TOPDIR)/SOURCES
	-mkdir -p $(TOPDIR)/RPMS/$(ARCH)

	# Copy the tarballs from PCC and put into roll automatically.

	-cp /pcc/internet/ftp.platform.com/lsfuser/distrib/$(VERSION)/platform_lsf/lsf$(VERSION).1_lsfinstall.tar.Z $(TOPDIR)/BUILD

	tar zxvf $(TOPDIR)/BUILD/lsf$(VERSION).1_lsfinstall.tar.Z -C $(TOPDIR)/BUILD

	-cp /pcc/internet/ftp.platform.com/lsfuser/distrib/$(VERSION)/platform_lsf/lsf$(VERSION).1_linux2.6-glibc2.3-x86_64.tar.Z $(TOPDIR)/BUILD/lsf7.0.1_lsfinstall/

	@echo "LSF_TOP=/opt/lsf" > $(TOPDIR)/BUILD/lsf7.0.1_lsfinstall/inst.conf
	@echo "LSF_MASTER_LIST=XXX_lsfmc_XXX" >> $(TOPDIR)/BUILD/lsf7.0.1_lsfinstall/inst.conf
	@echo "LSF_ADMINS=lsfadmin" >> $(TOPDIR)/BUILD/lsf7.0.1_lsfinstall/inst.conf
	@echo "LSF_CLUSTER_NAME=XXX_clustername_XXX" >> $(TOPDIR)/BUILD/lsf7.0.1_lsfinstall/inst.conf
	@echo "LSF_TARDIR=$(TOPDIR)/BUILD/lsf7.0.1_lsfinstall" >> $(TOPDIR)/BUILD/lsf7.0.1_lsfinstall/inst.conf
	@echo "EGO_DAEMON_CONTROL=N" >> $(TOPDIR)/BUILD/lsf7.0.1_lsfinstall/inst.conf
	@echo "LSF_LICENSE=$(TOPDIR)/BUILD/lsf7.0.1_lsfinstall/license.dat" >> $(TOPDIR)/BUILD/lsf7.0.1_lsfinstall/inst.conf
	@echo "LSF_QUIET_INST=Y" >> $(TOPDIR)/BUILD/lsf7.0.1_lsfinstall/inst.conf
	@echo "ENABLE_HPC_INST=Y" >> $(TOPDIR)/BUILD/lsf7.0.1_lsfinstall/inst.conf

	cp license.dat $(TOPDIR)/BUILD/lsf7.0.1_lsfinstall/

	if [ -z "$(CLUSTERNAME)" ]; then \
	   echo "Appending XXX_lsfmc_XXX host entry to /etc/hosts..." ;\
	   echo -e "w.x.y.z\t\tXXX_lsfmc_XXX" >> /etc/hosts ;\
	else \
	   echo "Using $(CLUSTERNAME) " ; \
	fi

	if [ `grep -c lsfadmin /etc/passwd` -eq 0 ]; then \
	   useradd lsfadmin ; \
	fi

	(cd $(TOPDIR)/BUILD/lsf7.0.1_lsfinstall; \
	 grep show_copyright lsfinstall -v > lsfinstall.tmp; \
         mv lsfinstall.tmp lsfinstall; \
         chmod 755 ./lsfinstall ; \
	 echo -e "y\n\n" | ./lsfinstall -f ./inst.conf)

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
