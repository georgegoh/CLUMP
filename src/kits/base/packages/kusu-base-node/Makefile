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
NAME = kusu-base-node

SPECFILES = `find . -maxdepth 1 -type f -name "*.spec"`
TOPDIR = $(PWD)/../..
ARCH=$(shell arch)


rpm:
	-mkdir -p $(TOPDIR)/BUILD/$(NAME)
	@echo "Tarring $(NAME)"
	tar cf - . |(cd $(TOPDIR)/BUILD/$(NAME) ; tar xf - )
	@if [ -f $(HOME)/.rpmmacros ] ; then \
		mv $(HOME)/.rpmmacros $(HOME)/.rpmmacros.OFF ; \
	fi
	echo "%_topdir $(TOPDIR)" > $(HOME)/.rpmmacros
	for i in $(SPECFILES) ; do \
		(rpmbuild -bb $$i ) ;\
	done
	# @rm -rf $(HOME)/.rpmmacros


cfmd:	
	cd cfm ;make cfmd

install::
	mkdir -p $(ROOT)/etc
	mkdir -p $(ROOT)/etc/init.d
	mkdir -p $(ROOT)/etc/rc.kusu.d
	mkdir -p $(ROOT)/etc/rc.kusu.custom.d
	mkdir -p $(ROOT)/opt/kusu/lib/python/kusu
	mkdir -p $(ROOT)/opt/kusu/sbin
	mkdir -p $(ROOT)/opt/kusu/etc
	install -m755 sbin/rc.kusu.sh $(ROOT)/etc/init.d/kusu
	install -m644 lib/kusu/ipfun.py $(ROOT)/opt/kusu/lib/python/kusu/
	install -m644 lib/kusu/__init__.py $(ROOT)/opt/kusu/lib/python/kusu/
	install -m755 sbin/cfmclient.py $(ROOT)/opt/kusu/sbin/cfmclient
	install -m755 cfm/cfmd $(ROOT)/opt/kusu/sbin/cfmd
