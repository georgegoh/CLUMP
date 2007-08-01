# 
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


RELEASE = 1
ROOT = 
NAME = initrd-templates

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
	mkdir -p $(ROOT)/opt/kusu/initrds/
	mkdir -p $(ROOT)/opt/kusu/etc/
	install -m644 initrds/rootfs.x86_64.cpio.gz $(ROOT)/opt/kusu/initrds/
	install -m644 initrds/rootfs.i686.cpio.gz $(ROOT)/opt/kusu/initrds/
	install -m755 etc/depmod.pl $(ROOT)/opt/kusu/etc/
	install -m755 etc/imageinit.py $(ROOT)/opt/kusu/etc/
	install -m755 etc/imageinit.sh $(ROOT)/opt/kusu/etc/

initrd-32bit:
	@echo "*************************************************************"
	@echo "*   WARNING:  Some parts of this build may be interactive!  *"
	@echo "*************************************************************"
	@if [ -d buildroot ]; then \
		rm -rf buildroot ; \
	fi
	@tar jxf ../../../../3rdparty/buildroot/buildroot*.bz2
	(cd 32bit ;cp .config* ../buildroot)
	(cd 32bit/packages ;cp -fr * ../../buildroot/packages/ )
	(cd buildroot ; make)
	(cd 32bit ;cp .config.cmd-withparted ../buildroot/.config.cmd)
	(cd 32bit ;cp .config-withparted ../buildroot/.config)
	(cd buildroot ; make)
	cp buildroot/rootfs.i686.cpio initrds/
	(cd initrds ;gzip rootfs.i686.cpio)

initrd-64bit:
	@echo "*************************************************************"
	@echo "*   WARNING:  Some parts of this build may be interactive!  *"
	@echo "*************************************************************"
	@if [ -d buildroot ]; then \
		rm -rf buildroot ; \
	fi
	@tar jxf ../../../../3rdparty/buildroot/buildroot*.bz2
	(cd 64bit ;cp .config* ../buildroot)
	(cd 64bit/packages ;cp -fr * ../../buildroot/packages/ )
	(cd buildroot ; make)
	(cd 64bit ;cp .config.cmd-withparted ../buildroot/.config.cmd)
	(cd 64bit ;cp .config-withparted ../buildroot/.config)
	(cd buildroot ; make)
	cp buildroot/rootfs.x86_64.cpio initrds/
	(cd initrds ;gzip rootfs.x86_64.cpio)