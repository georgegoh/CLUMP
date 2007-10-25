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
NAME = lsf-linux
PACKAGENAME = lsf-linux2.6-glibc2.3-x86_64-7.0.1-88401.rpm
VERSION = 7.0.1

TOPDIR = $(PWD)/../..
ARCH=$(shell arch)

rpm:
	-mkdir -p $(TOPDIR)/RPMS/$(ARCH)
	# Copy the tarballs from PCC and put into roll automatically.

	cp /pcc/lsf_madison/SOMEDIR/$(VERSION)/$(PACKAGENAME) $(TOPDIR)/RPMS/$(ARCH)

clean:
	if [ -f $(TOPDIR)/RPMS/$(ARCH)/$(PACKAGENAME) ]; then \
		rm -rf $(TOPDIR)/RPMS/$(ARCH)/$(PACKAGENAME) ; \
	fi
