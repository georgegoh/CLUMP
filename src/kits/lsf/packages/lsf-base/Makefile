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
BINARY_ARCH=linux2.6-glibc2.3-x86_64

SPECFILES = `find . -maxdepth 1 -type f -name "*.spec"`
TOPDIR = $(PWD)/../..
ARCH=$(shell arch)
export CLUSTERNAME=$(shell grep XXX_lsfmc_XXX /etc/hosts | sed -e "s/^[ \t]*\#.*//g")

LSFSRCDIR=/pcc/internet/ftp.platform.com/lsfuser/distrib/7.0/platform_lsf_update2

LSFINSTALL_TGZ=lsf7Update2_lsfinstall.tar.Z
LSFPLATFORM_TGZ=lsf7Update2_$(BINARY_ARCH).tar.Z

LSFDESTDIR=lsf7Update2_lsfinstall

rpm: preinstall install postinstall buildrpm

preinstall:
	-mkdir -p $(TOPDIR)/BUILD
	-mkdir -p $(TOPDIR)/SOURCES
	-mkdir -p $(TOPDIR)/RPMS/$(ARCH)
	rm -rf /opt/lsf

	# Copy the tarballs from PCC and put into kit automatically.
	-cp $(LSFSRCDIR)/$(LSFINSTALL_TGZ) $(TOPDIR)/BUILD
	tar zxf $(TOPDIR)/BUILD/$(LSFINSTALL_TGZ) -C $(TOPDIR)/BUILD
	-cp $(LSFSRCDIR)/$(LSFPLATFORM_TGZ) $(TOPDIR)/BUILD/$(LSFDESTDIR)

	@echo "LSF_TOP=/opt/lsf" > $(TOPDIR)/BUILD/$(LSFDESTDIR)/inst.conf
	@echo "LSF_MASTER_LIST=XXX_lsfmc_XXX" >> $(TOPDIR)/BUILD/$(LSFDESTDIR)/inst.conf
	@echo "LSF_ADMINS=lsfadmin" >> $(TOPDIR)/BUILD/$(LSFDESTDIR)/inst.conf
	@echo "LSF_CLUSTER_NAME=XXX_clustername_XXX" >> $(TOPDIR)/BUILD/$(LSFDESTDIR)/inst.conf
	@echo "LSF_TARDIR=$(TOPDIR)/BUILD/$(LSFDESTDIR)" >> $(TOPDIR)/BUILD/$(LSFDESTDIR)/inst.conf
	@echo "EGO_DAEMON_CONTROL=N" >> $(TOPDIR)/BUILD/$(LSFDESTDIR)/inst.conf
	@echo "LSF_LICENSE=$(TOPDIR)/BUILD/$(LSFDESTDIR)/license.dat" >> $(TOPDIR)/BUILD/$(LSFDESTDIR)/inst.conf
	@echo "LSF_QUIET_INST=Y" >> $(TOPDIR)/BUILD/$(LSFDESTDIR)/inst.conf
	@echo "ENABLE_HPC_INST=Y" >> $(TOPDIR)/BUILD/$(LSFDESTDIR)/inst.conf

	cp license.dat $(TOPDIR)/BUILD/$(LSFDESTDIR)/

	if [ -z "$(CLUSTERNAME)" ]; then \
		echo "Appending XXX_lsfmc_XXX host entry to /etc/hosts..." ;\
		echo -e "w.x.y.z\t\tXXX_lsfmc_XXX" >> /etc/hosts ;\
	else \
		echo "Using $(CLUSTERNAME) " ; \
	fi

	if [ `grep -c lsfadmin /etc/group` -eq 0 ]; then \
	   groupadd -g 495 lsfadmin; \
	fi

	if [ `grep -c lsfadmin /etc/passwd` -eq 0 ]; then \
	   adduser -u 495 -d "/home/lsfadmin" -g lsfadmin -m lsfadmin ;\
	fi

install:
	(cd $(TOPDIR)/BUILD/$(LSFDESTDIR); \
	 sed -i -e "/show_copyright/d" lsfinstall; \
	 echo -e "y\n\n" | ./lsfinstall -f ./inst.conf)

postinstall:
	# Remove junk from profile.lsf introduced by lsfinstall
	sed -i -e "/::::::::::::::/,/::::::::::::::/d" /opt/lsf/conf/profile.lsf
	sed -i -e "/::::::::::::::/,/::::::::::::::/d" /opt/lsf/conf/cshrc.lsf

	# Copy templates files
	@echo "Copying LSF \"template\" configuration files"
	rm -rf $(TOPDIR)/templates
	mkdir $(TOPDIR)/templates

	# Clean remnants from lsfinstall procedure
	rm -rvf /opt/lsf/conf/*.old
	rm -rvf /opt/lsf/conf/*.old*
	rm -rvf /opt/lsf/conf/lsbatch/XXX_clustername_XXX/configdir/*.old*

	# Copy template EGO cfg files
	[ -d $(TOPDIR)/templates/ego/default ] || mkdir -p $(TOPDIR)/templates/ego/default
	cp -ar /opt/lsf/conf/ego/XXX_clustername_XXX/* $(TOPDIR)/templates/ego/default/

    # LSF configuration
	cp /opt/lsf/conf/lsf.conf $(TOPDIR)/templates/default.lsf.conf
	cp /opt/lsf/conf/lsf.cluster.XXX_clustername_XXX $(TOPDIR)/templates/default.lsf.cluster
	cp /opt/lsf/conf/lsf.shared $(TOPDIR)/templates/default.lsf.shared

	# Build template version of the lsbatch directory/cfg files
	/usr/bin/install -d -d $(TOPDIR)/templates/lsbatch/default/configdir

	cp -ar /opt/lsf/conf/lsbatch/XXX_clustername_XXX/configdir/* $(TOPDIR)/templates/lsbatch/default/configdir/

	@echo "Tarring $(NAME)"
	tar cf - . |(cd $(TOPDIR)/BUILD/ ; tar xf - )

buildrpm:
	@if [ -f $(HOME)/.rpmmacros ] ; then \
		mv $(HOME)/.rpmmacros $(HOME)/.rpmmacros.OFF ; \
	fi

	echo "%_topdir $(TOPDIR)" > $(HOME)/.rpmmacros

	for i in $(SPECFILES) ; do \
		(rpmbuild -bb $$i ) ;\
	done

cleanup:
	# Cleanup /etc/hosts
	sed -i -e '/^w\.x\.y\.z.*/d' /etc/hosts

clean::
	@echo "Cleaning up..."

.PHONY: install clean rpm
