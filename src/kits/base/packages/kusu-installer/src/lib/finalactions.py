#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
from kusu.util.verify import *
from kusu.util.errors import *
from path import path
from IPy import IP
from Cheetah.Template import Template
import kusu.util.log as kusulog
logger = kusulog.getKusuLog('installer.final')

def setupDisks(disk_profile):
    logger.debug('Final action: Disk commit')
    disk_profile.commit(ignore_errors=True)
    disk_profile.formatAll()
 
def setupNetwork():
    # Use dhcpc from busybox
    # Assume eth0 for now
    from kusu.networktool import networktool

    interface = networktool.Interface('lo')
    interface.up()
    #interface = interface.setStaticIP(('127.0.0.1', '255.0.0.0'))

    #interface = networktool.Interface('eth0')
    #interface.up()
    #interface = interface.setDHCP()
   
def makeRepo(kiprofile):
    from kusu.repoman.repofactory import RepoFactory

    db = kiprofile.getDatabase()
    rfactory = RepoFactory(db, kiprofile['Kusu Install MntPt'])
    ngname = 'installer' + '-' + kiprofile['Kits']['longname']
    reponame = kiprofile['Kits']['longname']

    logger.debug('Making repo')

    repo = db.Repos()
    repo.reponame = reponame
    row = db.AppGlobals.select_by(kname = 'PrimaryInstaller')[0]
    masterNode = db.Nodes.select_by(name=row.kvalue)[0]
    repo.installers = ';'.join([nic.ip for nic in masterNode.nics if nic.ip])
    repo.kits = db.Kits.select()
    repo.ostype = '%s-%s-%s' % (kiprofile['OS'], kiprofile['OS_VERSION'], kiprofile['OS_ARCH'])
    repo.save()
    repo.flush()

    location = path('/depot/repos/%s' % repo.repoid)
    (path(kiprofile['Kusu Install MntPt']) / 'depot' / 'repos' / str(repo.repoid)).makedirs()
    repo.repository = str(location)
    repo.save()
    repo.flush()

    ng = db.NodeGroups.select_by(ngname = ngname)[0]    
    ng.repoid = repo.repoid
    ng.save()
    ng.flush()
    
    r = rfactory.getRepo(repo.repoid)
    r.refresh(repo.repoid)

    logger.debug('Making symlink to $KUSU_TMP/www.')
    #Makes symlink in $KUSU_TMP/www
    kusu_tmp = os.environ.get('KUSU_TMP', None)
    (path(kiprofile['Kusu Install MntPt']) / 'depot').symlink(path(kusu_tmp) / 'www')

    logger.debug('Finalising repo.')
    # workaround for starting repoIDs at 1000
    db.Repos.selectfirst_by(repoid=999).delete()
    db.flush()

def getPackageProfile(dbs, ngname):
    # Code adapted from autoinstall/installprofile.py.
    # There can only be 1 installer. Guaranteed by the db. 
    installer = dbs.NodeGroups.select_by(ngname=ngname)[0]
    try:
        components = [component.cname for component in installer.components \
                      if not component.kit.isOS]

        pkgs = [pkg.packagename for pkg in installer.packages]

        # also add all kit RPMs
        kitrpms = ["kit-%s" % kit.rname
                   for kit in dbs.Kits.select()
                   if not kit.isOS]

        return components + pkgs + kitrpms
    except AttributeError:
        raise AttributeError, 'components: %s' % str(installer.components)

def genAutoInstallScript(disk_profile, kiprofile):
    from primitive.installtool.commands import GenerateAutoInstallScriptCommand

    kusu_tmp = path(os.environ.get('KUSU_TMP', '/tmp'))
    kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
    kusu_dist = os.environ.get('KUSU_DIST', None)
    kusu_distver = os.environ.get('KUSU_DISTVER', None)

    if kusu_dist in ['fedora', 'centos', 'rhel']:
        install_script = kusu_tmp / 'kusu-ks.cfg'
    elif kusu_dist == "sles":
        install_script = kusu_tmp / 'kusu-autoinst.xml'
    else:
        install_script = kusu_tmp / 'install_script'

    if kiprofile.has_key('Network'):
        networkprofile = kiprofile['Network']

        row = kiprofile.getDatabase().AppGlobals.select_by(kname = 'InstallerServeDNS')[0]
        if row.kvalue == '1':
            networkprofile['dns1'] = '127.0.0.1'
            if networkprofile.has_key('dns2'): del networkprofile['dns2']
            if networkprofile.has_key('dns3'): del networkprofile['dns3']

    else:
        networkprofile = {}

    dbs = kiprofile.getDatabase()
    ngname = 'installer-' + kiprofile['Kits']['longname']
    packages = getPackageProfile(dbs, ngname)

    if kusu_dist == "sles":
        template_uri = 'file://%s' % (kusu_root / 'etc' / 'templates' / 'autoinst.tmpl')
    else:
        template_uri = 'file://%s' % (kusu_root / 'etc' / 'templates' / 'kickstart.tmpl')

    if kiprofile.has_key('InstNum'):
        instnum = kiprofile['InstNum']
    else:
        instnum = None


    # Note: installsrc is needed for rhel/centos but not for sles
    ic = GenerateAutoInstallScriptCommand(os={'name':kusu_dist, 'version':kusu_distver},
                                          diskprofile=disk_profile,
                                          networkprofile=networkprofile,
                                          installsrc='http://127.0.0.1/',
                                          rootpw=kiprofile['RootPasswd'],
                                          tz=kiprofile['Timezone']['zone'],
                                          lang=kiprofile['Language'],
                                          keyboard=kiprofile['Keyboard'],
                                          packageprofile=packages,
                                          instnum=instnum,
                                          diskorder=kiprofile['Partitions']['disk_order'],
                                          template_uri=template_uri,
                                          outfile=install_script)

    ic.execute()

def migrate(prefix):
    dest = path(prefix) + '/root'
    
    kusu_tmp = os.environ.get('KUSU_TMP', '/tmp/kusu')
    kusu_log = os.environ.get('KUSU_LOGFILE', '/var/log/kusu/kusu.log')

    kusu_tmp = path(kusu_tmp)
    kusu_log = path(kusu_log)

    files = ['kusu.db']
    files = [ kusu_tmp / f for f in files] + [kusu_log]
    for f in files:
        if f.exists():
            logger.info('Moved %s -> %s' % (f, dest))
            f.move(dest)

    files = ['kusu-ks.cfg', 'install_script', 'kusu-autoinst.xml']
    files = [ kusu_tmp / f for f in files] 
    for f in files:
        if f.exists():
            logger.info('Copied %s -> %s' % (f, dest))
            f.copy(dest)


def mountKusuMntPts(prefix, disk_profile):
    prefix = path(prefix)

    d = disk_profile.mountpoint_dict
    mounted = []

    # Mount and create in order 
    # fix bug 107818 - add /var to the list so that the lock file is touched
    # in the mounted partition if it exists. 
    for m in ['/', '/root', '/depot', '/depot/repos', '/depot/kits','/var']:
        mntpnt = prefix + m

        if not mntpnt.exists():
            mntpnt.makedirs()
            logger.debug('Made %s dir' % mntpnt)
        
        # mountpoint has an associated partition,
        # and mount it at the mountpoint
        if d.has_key(m):
            try:
                d[m].mount(mntpnt)
                mounted.append(m)
            except MountFailedError, e:
                raise MountFailedError, 'Unable to mount %s on %s' % (d[m].path, m)

    for m in ['/', '/depot']:
        if m not in mounted:
            raise KusuError, 'Mountpoint: %s not defined' % m


def writeNTP(prefix, kiprofile):
    prefix = path(prefix)
    
    ntp = path(prefix / 'etc' / 'ntp.conf')
    if not ntp.parent.exists():
        ntp.parent.makedirs()

    kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
    src = kusu_root / 'etc' / 'templates' / 'ntp.conf.tmpl'

    servers = []
    if kiprofile['Timezone']['ntp_server']:
        servers.append(kiprofile['Timezone']['ntp_server'])
    
    restrictNets = {}
    for intf, v in kiprofile['Network']['interfaces'].items():
        # interface is being configured, use static ip and activated on boot
        if v['configure'] and not v['use_dhcp'] and v['active_on_boot']:
            network = IP(v['ip_address']).make_net(v['netmask']).strNormal(0)
            restrictNets[network] = v['netmask']
    
    try:
        t = Template(file=str(src), searchList=[{'restrictNets':restrictNets,'servers':servers}])
        f = open(ntp, 'w')
        f.write(str(t))
        f.close()
        logger.info('Created ntp.conf')
    except:
        if ntp.exists():
            ntp.remove()
        logger.warn('Unable to create ntp.conf')

def setInstallFlag(prefix, kiprofile):
    prefix = path(prefix)
    flag = prefix / 'var' / 'lock' / 'subsys' /  'kusu-installer'
    # fix issue where the lock dir can already exist, causing an expection
    if not flag.parent.exists():
        flag.parent.makedirs()
    flag.touch()
