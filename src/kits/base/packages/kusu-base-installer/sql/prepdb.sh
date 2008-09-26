#!/bin/sh

# $Id: prepdb.sh 1438 2007-06-19 12:41:44Z ltsai $
#
#  Copyright (C) 2007 Platform Computing
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

# Create default database
/usr/bin/mysqladmin drop kusudb
/usr/bin/mysqladmin create kusudb
/usr/bin/mysql kusudb < ./kusu_createdb.sql
/usr/bin/mysql kusudb < ./kusu_alterdb.sql

# Set some sample values in the database table
/usr/bin/mysql kusudb < ./kusu_primedb_sample.sql

# Set user permissions
/usr/bin/mysql kusudb < ./kusu_dbperms.sql
