# Copyright (C) 2007 Platform Computing Inc
:#
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


lang:
	`cd po ; msgfmt -o kusuapps.mo en_US.po ; \
        cp kusuapps.mo ../locale/en/LC_MESSAGES/`

install::
	mkdir -p $(ROOT)/etc/cfm
	mkdir -p $(ROOT)/etc/rc.kusu.d
	mkdir -p $(ROOT)/var/www/html
	mkdir -p $(ROOT)/tftpboot/kusu/pxelinux.cfg
	mkdir -p $(ROOT)/opt/kusu/sbin
	mkdir -p $(ROOT)/opt/kusu/bin
	mkdir -p $(ROOT)/opt/kusu/cfm
	mkdir -p $(ROOT)/opt/kusu/etc
	mkdir -p $(ROOT)/opt/kusu/lib/python/kusu/ui/text
	mkdir -p $(ROOT)/opt/kusu/lib/python/kusu/ngedit
	mkdir -p $(ROOT)/opt/kusu/share/locale/en/LC_MESSAGES
	mkdir -p $(ROOT)/opt/kusu/sql
	mkdir -p $(ROOT)/opt/kusu/man/man8
	mkdir -p $(ROOT)/depot/repos/custom_scripts
	mkdir -p $(ROOT)/depot/kits
	mkdir -p $(ROOT)/depot/images
	# Just for development
	#echo "Letmein" > $(ROOT)/opt/kusu/etc/db.passwd
	touch $(ROOT)/depot/repos/custom_scripts/bogus.sh
	install -m644 sbin/S01KusuDB.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S90KusuCFM.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuDHCPD.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuRepo.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuSSH.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuSSHHosts.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuSyslog.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuApache.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuNfsExport.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S03KusuImage.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuIptables.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuNtp.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuXinetd.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuMotd.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuYumSetup.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuGenconfig.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuNamed.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuUsrSkel.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S02KusuZope.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m644 sbin/S90KusuFirefox.rc.py $(ROOT)/etc/rc.kusu.d/
	install -m755 sbin/boothost.py $(ROOT)/opt/kusu/sbin/boothost
	install -m755 sbin/buildimage.py $(ROOT)/opt/kusu/sbin/buildimage
	install -m755 sbin/buildinitrd.py $(ROOT)/opt/kusu/sbin/buildinitrd
	install -m755 sbin/addhost.py $(ROOT)/opt/kusu/sbin/addhost
	install -m755 sbin/cfmsync.py $(ROOT)/opt/kusu/sbin/cfmsync
	install -m755 sbin/netedit.py $(ROOT)/opt/kusu/sbin/netedit
	install -m755 sbin/ngedit $(ROOT)/opt/kusu/sbin/ngedit
	install -m755 sbin/nghosts.py $(ROOT)/opt/kusu/sbin/nghosts
	install -m755 sbin/nodeboot.cgi.py $(ROOT)/depot/repos/nodeboot.cgi
	install -m755 sbin/sqlrunner.py $(ROOT)/opt/kusu/sbin/sqlrunner
	install -m755 bin/genconfig.py $(ROOT)/opt/kusu/bin/genconfig
	install -m644 lib/kusu/__init__.py $(ROOT)/opt/kusu/lib/python/kusu
	install -m644 lib/kusu/nodefun.py $(ROOT)/opt/kusu/lib/python/kusu
	install -m644 lib/kusu/syncfun.py $(ROOT)/opt/kusu/lib/python/kusu
	install -m644 lib/kusu/addhost.py $(ROOT)/opt/kusu/lib/python/kusu
	install -m644 lib/kusu/cfms.py $(ROOT)/opt/kusu/lib/python/kusu
	install -m644 lib/kusu/cfmnet.py $(ROOT)/opt/kusu/lib/python/kusu
	install -m644 lib/kusu/genconfig.py $(ROOT)/opt/kusu/lib/python/kusu
	install -m644 lib/kusu/niifun.py $(ROOT)/opt/kusu/lib/python/kusu
	install -m644 lib/kusu/ngedit/ngedit.py $(ROOT)/opt/kusu/lib/python/kusu/ngedit
	install -m644 lib/kusu/ngedit/partition.py $(ROOT)/opt/kusu/lib/python/kusu/ngedit
	install -m644 lib/kusu/ngedit/__init__.py $(ROOT)/opt/kusu/lib/python/kusu/ngedit
	install -m644 lib/kusu/ui/text/USXkusuwidgets.py $(ROOT)/opt/kusu/lib/python/kusu/ui/text
	install -m644 lib/kusu/ui/text/USXnavigator.py $(ROOT)/opt/kusu/lib/python/kusu/ui/text
	install -m644 lib/kusu/ui/text/USXscreenfactory.py $(ROOT)/opt/kusu/lib/python/kusu/ui/text
	install -m644 sql/kusu_createdb.sql $(ROOT)/opt/kusu/sql
	install -m644 sql/kusu_dbperms.sql $(ROOT)/opt/kusu/sql
	install -m644 sql/kusu_alterdb.sql $(ROOT)/opt/kusu/sql
	install -m644 locale/en/LC_MESSAGES/kusuapps.mo $(ROOT)/opt/kusu/share/locale/en/LC_MESSAGES/
	install -m644 sql/kusu_primedb_sample.sql $(ROOT)/opt/kusu/sql
	install -m644 etc/index.tmpl $(ROOT)/var/www/html
	install -m755 sbin/index.py $(ROOT)/var/www/html
	cd man ;for i in `ls *.8`; do \
		gzip $$i ; \
		cp $$i.gz $(ROOT)/opt/kusu/man/man8/ ; \
	done
	echo "# CFM changed file list.  Generated automatically" > $(ROOT)/opt/kusu/cfm/changedfiles.lst
	#chown -R apache $(ROOT)/opt/kusu/cfm
