#   Copyright 2006 Platform Computing Inc
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   The license is also available in the source code under the license 
#   directory.
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

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
