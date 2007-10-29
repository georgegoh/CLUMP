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
# $Id$
#

NAME = cacti
ifndef ARCHIVE_SITE
ARCHIVE_SITE = http://www.osgdc.org/pub/build/kits
endif
KIT_ASSETS = $(ARCHIVE_SITE)/$(NAME)/sources

default: prep kit
	
prep:

	@echo "Please ensure buildkit and the kusu environment is set up properly!"
	@echo "Looking for buildkit.."
	@which buildkit

	cd sources && lftp -e "mget -c *  && quit" $(KIT_ASSETS)

kit:
	buildkit -v make kit=.
	
clean:
	-rm -rf artifacts/* kitinfo tmp/* packages/* kit-$(NAME)-*.iso
	
distclean: clean
	-rm -rf sources/*

	
