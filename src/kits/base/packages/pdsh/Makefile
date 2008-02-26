#   Copyright 2006 Platform Computing Inc
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

# $Log: Makefile,v $
# Revision 1.1.2.1  2006/10/31 19:48:49  sstarr
# Project #77475 - Add PDSH support to Extras roll
#
REDHAT.ROOT = $(PWD)/../..
TOPDIR = $(PWD)/../..

include version.mk

BASENAME = $(NAME)-$(VERSION)
rpm::
	-mkdir -p $(TOPDIR)/BUILD/$(NAME)
	@if [ -f $(HOME)/.rpmmacros ] ; then \
		mv $(HOME)/.rpmmacros $(HOME)/.rpmmacros.OFF ; \
	fi
	echo "%_topdir $(TOPDIR)" > $(HOME)/.rpmmacros
	# @rm -rf $(HOME)/.rpmmacros

	rpmbuild --rebuild --with dshgroups --with rsh --with ssh --with machines=/etc/hosts.pdsh $(BASENAME)-$(RELEASE).src.rpm
clean::
	rm -f ../../RPMS/i386/$(NAME)-$(VERSION)-$(RELEASE).i386.rpm
	rm -f ../../RPMS/x86_64/$(NAME)-$(VERSION)-$(RELEASE).x86_64.rpm
	rm -f ../../SRPMS/$(NAME)-$(VERSION)-$(RELEASE).src.rpm
