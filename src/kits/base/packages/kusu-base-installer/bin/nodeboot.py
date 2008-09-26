#!/usr/bin/python
#
# $Id: nodeboot.py 1641 2007-07-13 13:44:05Z mblack $
#
#   Copyright 2007 Platform Computing Inc
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

# This can be run by Apache, so be careful about paths!

from mod_python import apache


def hello(name=None):
    if name:
        return 'Hello, %s!' % name.capitalize()
    else:
        return 'Hello there!'

    
def handler(req):
    '''handler - This is the method Apache will call to run the request'''
    req.content_type = "text/plain"
    req.write("Hello World!")
    req.write("Nuts")
    
    return apache.OK
        
