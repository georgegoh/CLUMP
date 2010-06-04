#!/usr/bin/env python
#
# $Id$
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#

import sys
import os
import atexit
import cPickle as cpickle
from tempfile import mkdtemp

from path import path
from ConfigParser import ConfigParser

from primitive.support.yum import YumRepo
from primitive.fetchtool.commands import FetchCommand
from primitive.support.rpmtool import RPM
from primitive.core.errors import FetchException

from kusu.repoman import tools
from kusu.util.kits import processKitInfo

import kusu.util.log as kusulog
kl = kusulog.getKusuLog('kitops')

class RemoteKit(object):
    def __init__(self):
        super(RemoteKit, self).__init__()
        self.cachepath = path('/opt/kusu/var/cache/kitops')
        self.channel = 'rhn://rhel-x86_64-server-hpc-5/'

    def runListRemoteKit(self):
        kl.debug('Performing remote listing operation')

        headers = ['Kit', 'Kid', 'Description', 'Version', 'Release', 'Architecture', 'OS Kit',
                   'Removable', 'Supported OS', 'Repositories', 'Node Groups']

        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
        urlfile = kusu_root + '/etc/remoterepo.conf'
        cachepath = self.cachepath

        repodict= self.getRemoteRepoConfig(urlfile)

        for repo, url in repodict.iteritems():

            if not self.verifyCacheChecksum(repo, url):
                repoid = self.getMaxRepoID()
                self.cacheKitInfo(repo, repoid, url)

            repocache = cachepath.realpath()/repo

            for filename in repocache.files('*kitinfo*'):
                f = filename.basename()
                kit, components = processKitInfo(filename)
                os_set=set()
                if components:
                    for c in components:
                        for ostype in c['os']:
                            os_set.add(ostype['name']+'-'+ostype['major']+'.'+ostype['minor']+'-'+ostype['arch'])
                if kit:
                    print "%s:\t\t%s" % (headers[0], kit['name'])
                    print "%s:\t\t%s" % (headers[1], f[:f.find('_')])
                    print "%s:\t%s" % (headers[2], kit['description'])
                    print "%s:\t%s" % (headers[3], kit['version'])
                    print "%s:\t%s" % (headers[4], kit['release'])
                    print "%s:\t%s" % (headers[5], kit['arch'])
                    print "%s:\t%s" % (headers[9], repo)
                    print "%s:\t%s" % (headers[7], kit['removable'])
                    print "%s:\t%s" % (headers[8], ', '.join(os_set))
                    sys.stdout.write('\n\n')

    def runAddRemoteKit(self, rkid):
        kl.debug('Performing remote add kits operation')

        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
        cachepath = kusu_root + '/var/cache/kitops'

        if not self.verifyKitUpdated(rkid):
            print "Remote repository has been updated and kit id may have changed. Please do kitops -r\n"
            sys.exit(-1)
        repo, rpmurl = self.retrieveCacheURL(rkid)
        cachedir = os.path.join(cachepath, repo)
        url, krpm = os.path.split(rpmurl)

        if cachedir:
            tmpdir = path(mkdtemp(suffix='-kitops'))

            for f in cachedir.files():
                if f.find(str(rkid)+'_kitinfo') >= 0:
                    kit, components = processKitInfo(f)

                    if kit.has_key('filenames'):
                        for c in kit['filenames']:

                            if repo == 'rhel':
                                self.getRHNFile(url, c, tmpdir)
                            else:
                                urlc = os.path.join(url, c)

                                fc = FetchCommand(uri=urlc,
                                                  fetchdir=False,
                                                  destdir=tmpdir,
                                                  overwrite=False)
                                status, dest = fc.execute()
            return tmpdir

    def getRemoteRepoConfig(self, urlfile):
        """read the .conf file at /opt/kusu/etc/remoterepo.conf and return dict with repo name and url"""

        if os.path.isfile(urlfile):
            repodict={}
            cp = ConfigParser()
            cp.read(urlfile)

            for section in cp.sections():
                if section == 'rhel':
                    if cp.get(section, 'enabled') == str(1) and os.path.isfile('/etc/sysconfig/rhn/systemid'):
                        p = cp.get(section, 'conf')
                        g = tools.getConfig(p)
                        repodict[section] = g[section]['url']
                        if cp.get(section, 'channel'):
                            self.channel = cp.get(section, 'channel')
                else:
                    if cp.get(section, 'enabled') == str(1):
                        repodict[section] = cp.get(section, 'url')
            return repodict

    def getMaxRepoID(self):
        """generate new repo id to ensure no duplication"""
        cachepath = self.cachepath
        rlist=[]

        for root, dirs, files in os.walk(cachepath, True):
            for f in files:
                if f.find('kitinfo') >=0:
                    rlist.append(int(f[:f.find('-')]))
                    break

        if rlist == []:
            return 1
        else:
            return max(rlist)+ 1

    def cacheKitInfo(self, repo, repoid, url):
        """cache the kitinfo files of all the kit rpm in the cache directory"""

        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
        cachepath = self.cachepath +'/'+ repo

        if not cachepath.isdir():
            os.makedirs(cachepath +'/repodata')

        self.cacheRepoMD(repo, url)

        if repo == 'rhel':
            self.getRHNFile(url, '/repodata/primary.xml.gz', cachepath)
            y = YumRepo('file://'+ cachepath)
        else:
            y = YumRepo(url)

        p = y.getPrimary()
        kitid = 1
        kitdict = {}
        for kit in p.keys():
            if kit.startswith('kit-'):

                for arch in p[kit].keys():
                    tempdir = path(mkdtemp(suffix='-kitops'))
                    atexit.register(lambda: tempdir.rmtree())
                    choice = p[kit][arch][0]

                    if repo == 'rhel':
                        pkg = choice.filename
                        self.getRHNFile(url, pkg.basename(), tempdir)
                        tmppath= tempdir +'/'+pkg.basename()
                        r = RPM(str(tmppath))
                        r.extract(tempdir)
                    else:
                        choice.extract(tempdir)

                    for file in tempdir.files():
                        if file.basename()=='kitinfo':
                            kit, components = processKitInfo(file)
                            kitdict[str(repoid)+'-'+ str(kitid)] = url +'/'+ kit['pkgname'] +'-'+ kit['version'] +'-'+ kit['release'] +'.'+kit['arch']+'.rpm'
                            os.rename(tempdir +'/kitinfo', cachepath +'/'+ str(repoid) +'-'+ str(kitid)+'_kitinfo')
                            kitid = kitid + 1
                            break

        self.generateCacheFile(repo, kitdict)
        return

    def cacheRepoMD(self, repo, url):
        """fetch the repomd.xml from repository and cache in the repo cache directory"""

        cachepath = self.cachepath +'/'+ repo

        if not cachepath.isdir():
            os.makedirs(cachepath +'/repodata')

        if repo == 'rhel':
            self.getRHNFile(url, '/repodata/repomd.xml', cachepath)
        else:
            fc = FetchCommand(uri=url +'/repodata/repomd.xml',
                              fetchdir=False,
                              destdir= cachepath +'/repodata',
                              overwrite=True)
            status, dest = fc.execute()

    def generateCacheFile(self, repo, kitdict):
        """create cachekits.pck from the kitdict with the rkid and url"""
        cachepath = self.cachepath +'/'+ repo

        if not cachepath.isdir():
            os.makedirs(cachepath)

        outfile = open(cachepath +'/cachekits.pck', 'wb')
        cpickle.dump(kitdict, outfile)
        outfile.close()

    def verifyKitUpdated(self, rkid):
        """check if the rkid of the kit to be added is up-to-date"""
        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
        cachepath = kusu_root + '/var/cache/kitops'

        root, kitdict = self.retrieveCacheKitURL(rkid)

        if root and kitdict:
            kpath, krepo = os.path.split(root)
            kurl, krpm = os.path.split(kitdict[rkid])
            return self.verifyCacheChecksum(krepo, kurl)
        return False

    def retrieveCacheKitURL(self, rkid):
        """return the root path of the cachekit.pck file and the rkid, kit url in dict form"""
        cachepath = self.cachepath

        for root, dirs, files in os.walk(cachepath, True):
           if files.count('cachekits.pck') > 0:
               f = os.path.join(root, 'cachekits.pck')
               if os.path.isfile(f):
                   infile = open(f, 'rb')
                   kitdict = cpickle.load(infile)

                   for i in kitdict.keys():
                       if i == rkid:
                           infile.close()
                           return root, kitdict
                   infile.close()
        return "", {}

    def verifyCacheChecksum(self, repo, url):
        """check if the cache repo information is updated by fetching repomd.xml and comparing the checksums"""
        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
        cachepath = self.cachepath +'/'+ repo

        if cachepath.isdir():
            r={}
            l={}
            local = YumRepo('file://'+ cachepath)
            try:
                l=local.getRepoMD()
            except FetchException, e:
                kl.error(e)
                print "Unable to retrieve repomd.xml file in cache directory [%s]\n" % repo

            if repo == 'rhel':
                tmpdir = path(mkdtemp(suffix='-kitops'))
                atexit.register(lambda: tmpdir.rmtree())
                self.getRHNFile(url, '/repodata/repomd.xml', tmpdir)
                remote=YumRepo('file://'+ tmpdir)
                try:
                    r=remote.getRepoMD()
                except FetchException, e:
                    kl.error(e)
                    print "Unable to access rhhpc server\n"
            else:
                remote = YumRepo(url)
                try:
                    r=remote.getRepoMD()
                except FetchException, e:
                    kl.error(e)
                    print "Unable to access remote repository [%s]\n" % repo

            if l and r:
                return self.compareCheckSum(local.repo, remote.repo)
        return False

    def compareCheckSum(self, local, remote):
        """Compare the primary.xml.gz checksum value from the local repomd.xml
           and the remote repomd.xml"""
        return local['primary']['checksum'][0] == remote['primary']['checksum'][0] and \
               local['primary']['checksum'][1] == remote['primary']['checksum'][1]

    def getRHNFile(self, url, filename, dest):

        if not dest.isdir():
            os.makedirs(dest +'/repodata')

        if filename.find('repodata') >= 0:
            dest = dest + '/repodata'
            if not dest.isdir():
                os.makedirs(dest)

        if dest.isdir():
            fc = FetchCommand(uri=self.channel + filename,
                              fetchdir=False,
                              destdir=dest,
                              overwrite=True,
                              systemid=open('/etc/sysconfig/rhn/systemid', 'r'),
                              up2dateURL=url)
            status, dest = fc.execute()

    def retrieveCacheURL(self, rkid):
        """find the url of the remote kit from the rkid in the cachekits.pck"""

        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
        cachepath = kusu_root + '/var/cache/kitops'
        root, kitdict = self.retrieveCacheKitURL(rkid)

        return root.basename(), kitdict[rkid]
