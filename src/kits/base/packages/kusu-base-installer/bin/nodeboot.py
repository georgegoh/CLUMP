#!/usr/bin/python
#
# $Id$
#
#   Copyright 2007 Platform Computing Inc
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
#
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
        
