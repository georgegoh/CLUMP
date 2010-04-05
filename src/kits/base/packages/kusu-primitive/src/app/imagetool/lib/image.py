#!/usr/bin/env python
# $Id$
#
"""imagetool class and operations"""

from primitive.imagetool import helper
from primitive.core.command import CommandFailException
from primitive.support.util import runCommand
from tempfile import mkdtemp
from path import path

class ImageToolException(CommandFailException):
    """This class is always called in the context of a command and thus needs
    to inherit it"""
    pass
    
class ImageTool(object):

    def __init__(self, **kwargs):
        pass
        
    def createRootImgDir(self, src, dest, os, osver, osarch, 
            kernelpath, initrdpath):
        """Create a root image directory in dest out of the given src"""
        srcdir = path(src).abspath()
        destdir = path(dest).abspath()
        
        if not srcdir.exists():
            errmsg = '%s does not exists!'
            raise ImageToolException, errmsg
            
        # construct imginfo dict except for the archives list
        imgdict = {}
        imgdict['os'] = os
        imgdict['osver'] = osver
        imgdict['osarch'] = osarch
        imgdict['kernelpath'] = kernelpath
        imgdict['initrdpath'] = initrdpath
            
        #FIXME: Only handles subdirectories under /. Files are not packed!
        dirs = srcdir.dirs()
        
        # create scratchdir
        scratchdir = path(mkdtemp(suffix='-imgtool'))
        
        packdir = scratchdir / destdir.basename()
        packdir.mkdir()
        
        archiveslist = []
        for d in dirs:
            archivename = '%s.tgz' % d.basename()
            archivesize = helper.getDirSize(d)
            cmd = 'tar zcf %s/%s -C %s .%s' % (packdir, archivename, srcdir, d[len(srcdir):])
            err, out = runCommand(cmd)
            #FIXME: check error status!
            
            # construct the imginfo archives information
            adict = {}
            adict[archivename] = archivesize
            archiveslist.append(adict)
            
        imgdict['archives'] = archiveslist
        
        # generate the imginfo file
        imginfofile = packdir / 'imginfo'
        helper.generateImgInfo(imginfofile, imgdict)
        
        # nuke the existing destdir if any
        if destdir.exists(): destdir.rmtree()
        
        # rename the packdir as the destdir
        cmd = 'mv %s %s' % (packdir, destdir)
        
        err, out = runCommand(cmd)
        #FIXME: check error status!
        
        # remove scratchdir
        if scratchdir.exists(): scratchdir.rmtree()
        
        # FIXME: the output may be subject to change!
        output = {}
        output['status'] = err
        output['errmsg'] = ''
        output['imgdir'] = destdir
        output['imginfo'] = destdir / 'imginfo'
        
        return output
        
    #def createXenImage(self):
        
    #def createVmwareImage(self):

        
