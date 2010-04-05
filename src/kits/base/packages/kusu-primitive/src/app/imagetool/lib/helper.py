#!/usr/bin/env python
# $Id$
"""Helper methods for imagetool"""

import os
from path import path
import pprint

def _getsize(filename):
    """Return the size of a file, reported by os.stat(). This is a
    reimplmentation as the original version of os.getsize doesn't 
    handle links very well.
    """
    if os.path.islink(filename):
        # Do not calculate the size for symlinks
        return 0L
    return os.stat(filename).st_size


def getDirSize(directory):
    """Returns the total size in bytes of a directory (and all its contents)."""
    dirsize = 0
    for (p, dirs, files) in os.walk(directory):
        for f in files:
            filename = os.path.join(p, f)
            dirsize += _getsize(filename)
    return dirsize
    
def getImgInfo(imginfo):
    """Loads the imginfo file and returns a metainfo dict.
    """
    imginfo = path(imginfo)
    if not imginfo.isfile(): return {}

    ns = {}

    # If there is a syntax error in the imginfo file, holla!
    try:
        execfile(imginfo, ns)
    except SyntaxError, e:
        errmsg = "%s in kitinfo file %s at line %s, column %s" % \
                        (e.msg, e.filename, e.lineno, e.offset)
        # FIXME: Use the proper primitive exceptions!
        raise SyntaxError, errmsg

    d = ns.get('imginfo',{})

    return d
    
def generateImgInfo(filename, d):
    """ Generates an imginfo file."""
    
    try:
        f = open(filename,'w')
        f.write('imginfo = %s\n' % pprint.pformat(d))
        f.close()
    except IOError, e:
        errmsg = "I/O Error while writing to %s" % filename
        raise IOError, errmsg
        

        
        

    

    


