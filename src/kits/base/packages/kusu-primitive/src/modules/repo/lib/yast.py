#!/usr/bin/env python
#
# $Id: yast.py 3135 2009-10-23 05:42:58Z ltsai $
#

# Reference: 
#  http://en.opensuse.org/Creating_YaST_Installation_Sources
#  http://en.opensuse.org/Software_Repositories/YaST
#  http://www.suse.com/~ug/AutoYaST_FAQ.html

from path import path

import subprocess
import os
import re
import sha
import glob
import time
from tempfile import mkdtemp
from primitive.repo.errors import RepoException
from primitive.repo.errors import RepoCreationError
from primitive.repo.errors import RepoUpdateImgError
from primitive.fetchtool.commands import FetchCommand
from primitive.support.util import mountLoop
from primitive.support.util import unmount
from primitive.support.util import getFstype

class YastRepo(object):
    def __init__(self, repo_path,**unused):
        unused.clear() # get rid of unused args
        self.repo_path = path(repo_path)
        self.isOSMedia = self.checkOSMedia()

        if self.isOSMedia:
            self.pkg_descr_dir = self.repo_path / 'suse' / 'setup' / 'descr'
            self.data_dir = self.repo_path / 'suse'
        else:
            self.pkg_descr_dir = self.repo_path / 'setup' / 'descr'
            self.data_dir = self.repo_path 

    def make(self):
        self.makeMeta()
        self.makeContent()
        self.makeMedia()
        self.makeProducts()

        self.makeMD5(self.pkg_descr_dir)
        self.makeDirectoryYast(self.pkg_descr_dir)
        self.makeDirectoryYast(self.repo_path)
        self.makeDirectoryYast(self.repo_path / 'media.1')


    def makeMeta(self):

        if os.path.exists('/usr/bin/create_package_descr'): 
            cmd = 'perl /usr/bin/create_package_descr'
        else:
            cmd = 'create_package_descr'

        cmd = cmd + ' -d %s -o %s -l english' % (self.data_dir, self.pkg_descr_dir)

        extra_prov = self.pkg_descr_dir / 'EXTRA_PROV'
        if extra_prov.exists():
            cmd = cmd + ' -x %s' % extra_prov
       
        try:
            p = subprocess.Popen(cmd,
                                 cwd=self.repo_path,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode
        except Exception,e :
            raise RepoCreationError,'Failed to create repository : %s' % e

        if retcode:
            raise RepoCreationError,\
                   'Repository creation failed with return code  %d' % retcode
        
    def checkOSMedia(self):
        # FIXME: replace with distro detection from kusu

        if (self.repo_path / 'suse').exists() and \
            (self.repo_path / 'control.xml').exists() and \
            (self.repo_path / 'boot').exists():
            return True 
        else:
            return False 

    def makeContent(self):
        content = self.repo_path / 'content'

        if not content.exists():
            txt = """PRODUCT Primitive 
VERSION 1.0
LABEL Primitive (1.0)
VENDOR Primitive 
ARCH.i686 i686 i586 i486 i386 noarch
ARCH.i586 i586 i486 i386 noarch
DEFAULTBASE i586
DESCRDIR setup/descr
"""
            f = open(content, 'w')
            f.write(txt)
            f.close()
        else:
            if not content.exists():
                raise RepoException,'Error creatiing repository contents!'

        if self.isOSMedia:
            descr_path = self.repo_path / 'suse' / 'setup' / 'descr'
        else:
            descr_path = self.repo_path / 'setup' / 'descr'

        # clean up gz packages. Affects third party rpms in repo
        [ f.remove() for f in descr_path.glob('packages.*gz') ]
        if (descr_path / 'packages.DU').exists(): (descr_path / 'packages.DU').remove()
 
        # Update sha1sum for setup/descr/packages*
        f = open(content, 'r')
        lines = f.readlines()

        newLines = []
        for line in lines:
            if line.rfind('packages') == -1:
                newLines.append(line)

        for file in glob.glob(descr_path / 'packages*'):
            fd = open(file, 'r')
            digest = sha.new(fd.read()).hexdigest()
            fd.close()

            newLines.append('META SHA1 %s  %s\n' % (digest, os.path.basename(file)))
           
        fd = open(content, 'w')
        fd.writelines(newLines)
        fd.close()

        # remove content.asc and content.key for OS Media
        for file in glob.glob(content + '.*'):
            os.remove(file)

    def makeMedia(self):
        # media.1/media

        media = self.repo_path / 'media.1' / 'media'
        if not self.isOSMedia:
            if not media.parent.exists():
                media.parent.makedirs()

            f = open(media, 'w')
            f.write('primitive\n%s\n1\n' % time.strftime('%Y%m%d%H%M%S'))
            f.close()

    def writeMedia(self, vendor='primitive', timestamp=time.strftime('%Y%m%d%H%M%S'), mediacount=1):

        media = self.repo_path / 'media.1' / 'media'
        if not media.parent.exists():
            media.parent.makedirs()

        f = open(media, 'w')
        f.write('%s\n%s\n%s\n' % (vendor, timestamp, mediacount))
        f.close()

    def makeProducts(self):
        # media.1/products
       
        products = self.repo_path / 'media.1' / 'products'
        if not self.isOSMedia:
            if not products.parent.exists():
                products.parent.makedirs()

            f = open(products, 'w')
            f.write('/ primitive 1.0\n')
            f.close()

    def makeMD5(self, p):
        if (p / 'MD5SUMS').exists():
            (p / 'MD5SUMS').remove()

        
        cmd = 'md5sum * > MD5SUMS'
        try:
            p = subprocess.Popen(cmd,
                                 cwd=p,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode
        except Exception,e:
            raise RepoCreationError,'Failed to create repository : %s' % e

        if retcode:
            raise RepoCreationError,\
                   'Repository creation failed with return code  %d' % retcode

    def makeDirectoryYast(self, p):

        directory_yast = p / 'directory.yast'
        if directory_yast.exists():
            directory_yast.remove()

        fd = open(directory_yast, 'w')
        for file in p.listdir():
            if file.basename() != 'directory.yast':
                fd.write(file.basename() + '\n')
        fd.close()
            
    def updateRootfsSha1sum(self, rootfs):
        """Update sha1sum for rootfs in content file"""
        content = self.repo_path / 'content'

        # Get the sha1 checksum for rootfs
        rootfs_path = self.repo_path / rootfs
        digest = sha.new(rootfs_path.bytes()).hexdigest()

        # Use regexp to match end-of-line because there is another
        # similar entry 'boot/<arch>/root.fonts' in the content file
        pattern = re.compile(rootfs + '$')
        lines = [ line for line in content.lines() if not re.search(pattern, line) ]
        lines.append('HASH SHA1 %s  %s\n' % (digest, rootfs))
        content.write_lines(lines)

    def handleUpdates(self, update_uri):
        ''' Fetches the updates.img from update_uri and merges it into
            root image for sles.
        '''
        dl_dir = path(mkdtemp(prefix='RepoYastUpdate'))
        working_mnt = path(mkdtemp(prefix='RepoYastRootMnt'))
        working_rootimg = path(mkdtemp(prefix='RepoYastRootImg'))
        working_updateimg = path(mkdtemp(prefix='RepoYastUpdatesImg'))

        # Take root image from the pristine repository
        # and copy to a working location.
        bootdir_ls = (self.repo_path / 'boot' / 'directory.yast').open().readlines()
        arch = bootdir_ls[0].strip()
        rootfs = self.repo_path / 'boot' / arch / 'root'
        fstype = getFstype(rootfs)
        if fstype == 'squashfs':
            # if root image is squashfs, extract it to working directory.

            # squashfs will complain if the destination directory already exists.
            if working_rootimg.exists():
                working_rootimg.rmtree()
            args = ['unsquashfs', '-dest', working_rootimg, rootfs]
            p = subprocess.Popen(args,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
        else:
            # else, mount and copy.
            mountLoop(rootfs, working_mnt)
            fc = FetchCommand(uri='file://'+str(working_mnt), fetchdir=True,
                              destdir=working_rootimg, overwrite=True)
            fc.execute()
            unmount(working_mnt)

        # mount update image and copy to working location.
        fc = FetchCommand(uri=update_uri, fetchdir=False,
                          destdir=dl_dir, overwrite=True)
        update_path = fc.execute()[1]

        mountLoop(update_path, working_updateimg)
        fc = FetchCommand(uri='file://'+str(working_updateimg), fetchdir=True,
                          destdir=working_rootimg, overwrite=True)
        fc.execute()
        unmount(working_updateimg)

        fstype = getFstype(rootfs)
        if fstype == 'squashfs':
            app = 'mksquashfs'
            args = [app, 
                    str(working_rootimg),
                    rootfs,
                    '-noappend']
        else:
            # pack up modified root image via cramfs.
            app = 'mkfs.cramfs'
            args = [app, 
                    str(working_rootimg),
                    rootfs]

        p = subprocess.Popen(args,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        # clean up working directories
        working_updateimg.rmtree()
        working_rootimg.rmtree()
        working_mnt.rmtree()
        dl_dir.rmtree()

        rootfs_entry = path('boot') / arch / 'root'
        self.updateRootfsSha1sum(rootfs=rootfs_entry)

        if p.returncode:
            raise RepoUpdateImgError, \
                  '%s failed while creating new root image:\n %d:%s' \
                  % (app, p.returncode, stderr)

if __name__ == '__main__':

    repo = '/srv/www/htdocs/suse'
    y = YastRepo(repo)
    y.make()

    repo = '/srv/www/htdocs/test'
    y = YastRepo(repo)
    y.make()

