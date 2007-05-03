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
# 
# $Id$
# 


RELEASE = 1
ROOT = 
NAME = kusu-base-installer

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



install::
	mkdir -p $(ROOT)/etc/rc.kusu.d
	mkdir -p $(ROOT)/tftpboot/kusu/pxelinux.cfg
	mkdir -p $(ROOT)/opt/kusu/sbin
	mkdir -p $(ROOT)/opt/kusu/bin
	mkdir -p $(ROOT)/opt/kusu/cfm
	mkdir -p $(ROOT)/opt/kusu/etc
	mkdir -p $(ROOT)/opt/kusu/lib/kusu
	mkdir -p $(ROOT)/opt/kusu/lib/plugins/addhost 
	mkdir -p $(ROOT)/opt/kusu/lib/plugins/dbreport
	mkdir -p $(ROOT)/opt/kusu/lib/plugins/ngedit
	mkdir -p $(ROOT)/opt/kusu/locale/en/LC_MESSAGES
	mkdir -p $(ROOT)/opt/kusu/sql
	mkdir -p $(ROOT)/opt/kusu/man/man8
	mkdir -p $(ROOT)/repo/repos
	mkdir -p $(ROOT)/repo/repos/custom_scripts
	mkdir -p $(ROOT)/repo/kits
	mkdir -p $(ROOT)/repo/images
	install -m755 sbin/S01KusuSetup $(ROOT)/etc/rc.kusu.d/
	install -m755 sbin/boothost.py $(ROOT)/opt/kusu/sbin/boothost
	install -m755 sbin/buildimage.py $(ROOT)/opt/kusu/sbin/buildimage
	install -m755 sbin/buildinitrd.py $(ROOT)/opt/kusu/sbin/buildinitrd
	install -m755 sbin/addhost.py $(ROOT)/opt/kusu/sbin/addhost
	install -m755 sbin/nodeboot.cgi.py $(ROOT)/repo/repos/nodeboot.cgi
	install -m755 bin/dbreport.py $(ROOT)/opt/kusu/bin/dbreport
	install -m644 lib/kusu/__init__.py $(ROOT)/opt/kusu/lib/kusu
	install -m644 lib/kusu/ipfun.py $(ROOT)/opt/kusu/lib/kusu
	install -m644 lib/kusu/syncfun.py $(ROOT)/opt/kusu/lib/kusu
	install -m644 lib/kusu/kusudb.py $(ROOT)/opt/kusu/lib/kusu
	install -m644 lib/kusu/kusuapp.py $(ROOT)/opt/kusu/lib/kusu
	install -m644 lib/kusu/screens/kusuwidgets.py $(ROOT)/opt/kusu/lib/kusu/screens
	install -m644 lib/kusu/screens/navigator.py $(ROOT)/opt/kusu/lib/kusu/screens
	install -m644 lib/kusu/screens/screenfactory.py $(ROOT)/opt/kusu/lib/kusu/screens
	install -m644 lib/plugins/dbreport/__init__.py $(ROOT)/opt/kusu/lib/plugins/dbreport
	install -m644 lib/plugins/dbreport/apache_conf.py $(ROOT)/opt/kusu/lib/plugins/dbreport
	install -m644 lib/plugins/dbreport/debug.py $(ROOT)/opt/kusu/lib/plugins/dbreport
	install -m644 lib/plugins/dbreport/dhcpd.py $(ROOT)/opt/kusu/lib/plugins/dbreport
	install -m644 lib/plugins/dbreport/hosts.py $(ROOT)/opt/kusu/lib/plugins/dbreport
	install -m644 lib/plugins/dbreport/named.py $(ROOT)/opt/kusu/lib/plugins/dbreport
	install -m644 lib/plugins/dbreport/nodes.py $(ROOT)/opt/kusu/lib/plugins/dbreport
	install -m644 lib/plugins/dbreport/reverse.py $(ROOT)/opt/kusu/lib/plugins/dbreport
	install -m644 lib/plugins/dbreport/zone.py $(ROOT)/opt/kusu/lib/plugins/dbreport	
	install	-m644 lib/plugins/addhost/00-boothost.py $(ROOT)/opt/kusu/lib/plugins/addhost
	install	-m644 lib/plugins/addhost/01-hosts.py $(ROOT)/opt/kusu/lib/plugins/addhost
	install	-m644 lib/plugins/addhost/02-dnsreverse.py $(ROOT)/opt/kusu/lib/plugins/addhost
	install	-m644 lib/plugins/addhost/03-dnszone.py $(ROOT)/opt/kusu/lib/plugins/addhost
	install	-m644 lib/plugins/addhost/04-dhcp.py $(ROOT)/opt/kusu/lib/plugins/addhost
	install -m644 lib/plugins/ngedit/__init__.py $(ROOT)/opt/kusu/lib/plugins/ngedit
	install -m644 sql/kusu_createdb.sql $(ROOT)/opt/kusu/sql
	install -m644 sql/kusu_dbperms.sql $(ROOT)/opt/kusu/sql
	install -m644 sql/kusu_alterdb.sql $(ROOT)/opt/kusu/sql
	install -m644 sql/kusu_primedb_sample.sql $(ROOT)/opt/kusu/sql
	echo "# CFM changed file list.  Generated automatically" > $(ROOT)/opt/kusu/cfm/changedfiles.lst
	chown -R apache $(ROOT)/opt/kusu/cfm
