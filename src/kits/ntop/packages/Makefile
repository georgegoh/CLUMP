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

default: rpm

rpm:
	@echo "Building Ntop..."

	rpmbuild --rebuild cgilib-0.5-1.src.rpm
	@-rpm -ivh ../RPMS/$(ARCH)/cgilib-devel-0.5-1.$(ARCH).rpm
	rpmbuild --rebuild rrdtool-1.2.23-1.src.rpm --define "_prefix /opt/ntop"
	@-rpm -ivh ../RPMS/$(ARCH)/perl-rrdtool-1.2.23-1.$(ARCH).rpm ../RPMS/$(ARCH)/rrdtool-1.2.23-1.$(ARCH).rpm
	@-rpm -ivh ../RPMS/$(ARCH)/rrdtool-devel-1.2.23-1.$(ARCH).rpm
	rpmbuild --rebuild ntop-3.3-1.src.rpm  --define "dist el5" --define "_prefix /opt/ntop" --define "_initrddir /etc/init.d" --define "_sysconfdir /etc"
clean:
