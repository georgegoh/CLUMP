import subprocess
from path import path
from kusu.util import rpmtool
from kusu.buildkit import processKitInfo
from kusu.util.errors import KitAlreadyInstalledError,ComponentAlreadyInstalledError

import kusu.util.log as kusulog
kl = kusulog.getKusuLog('kitops')

def addkit01(koinst, db, kitinfo):
    kitpath = path(kitinfo[0])
    kit = kitinfo[1]
    kitrpm = '%s-%s-%s.%s.rpm' % (kit['pkgname'], kit['version'],
                                  kit['release'], kit['arch'])

    #check if this kit is already installed - by name, version, release and arch
    if checkKitInstalled01(koinst, db, kit['name'], kit['version'], kit['arch']):
        raise KitAlreadyInstalledError, \
                "Cannot install kit '%s-%s-%s-%s' due to a conflicting kit already installed." % \
                (kit['name'], kit['version'], kit['release'], kit['arch'])


    # populate the kit DB table with info
    newkit = db.Kits(rname=kit['name'], rdesc=kit['description'],
                     version=kit['version'], arch=kit['arch'],
                     removable=kit['removable'])
    newkit.save()

    db.flush()
    kl.debug('Addkit kid: %s', newkit.kid)

    # copy the RPMS
    repodir = koinst.kits_dir / str(newkit.kid)
    if not repodir.exists():
        repodir.makedirs()

    srcP = subprocess.Popen('tar cf - *.rpm', cwd=kitpath,
                            shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    dstP = subprocess.Popen('tar xf -',
                            cwd=repodir, shell=True, stdin=srcP.stdout,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dstP.communicate()

    # also copy the kitinfo file
    kifile = kitpath / 'kitinfo'
    if kifile.exists(): kifile.copy(repodir)

    
    # check/populate component table
    try:
        updated_ngs = koinst.updateComponents(newkit, kitinfo[2])
    except ComponentAlreadyInstalledError, msg:
        # updateComponents encountered an error, remove kit from DB
        newkit.removable = True
        newkit.flush()
        koinst.deleteKit(del_name=kit['name'], del_version=kit['version'], del_arch=kit['arch'])
        raise ComponentAlreadyInstalledError, msg
            
    # install the kit RPM
    if not koinst.installer:
        rpmP = subprocess.Popen('rpm --quiet --force --nodeps -i %s' %
                                (kitpath / kitrpm),
                                shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        o, e = rpmP.communicate()
        kl.debug('Installing kit RPM stdout: %s, stderr: %s', o, e)

        if rpmP.returncode != 0:
            # failed installing RPM, remove kit from DB
            newkit.removable = True
            newkit.update()
            newkit.flush()
            koinst.deleteKit(kit['name'], kit['version'], kit['arch'])
            raise InstallKitRPMError, 'Kit RPM installation ' + \
                'failed, return code: %d' % rpmP.returncode
    else:
        rpm = kitinfo[3]

        # execute pre section
        cfmsync = koinst.addRPMPreScript(kit['name'],
                                         kit['version'],
                                         kit['arch'],
                                         rpm.getPre())

        # execute post section
        cfmsync = koinst.addRPMPostScript(kit['name'],
                                          kit['version'],
                                          kit['arch'],
                                          rpm.getPost()) or cfmsync

        if cfmsync: koinst.add_cfmsync_script()

    return newkit.kid, updated_ngs


def checkKitInstalled01(koinst, db, kitname, kitver, kitarch):
    """
    Returns True if specified kit is already in the DB, False otherwise.
    """
    matches = db.Kits.select_by(rname=kitname)
    for m in matches:
        m_api = koinst.getKitApi(m.kid)
        if m_api == '0.1' and m.version == kitver and m.arch == kitarch:
            return True
        if m_api == '0.2':
            return True
    return False


def addkit02(koinst, db, kitinfo):
    kitpath = path(kitinfo[0])
    kit = kitinfo[1]
    kitrpm = '%s-%s-%s.%s.rpm' % (kit['pkgname'], kit['version'],
                                  kit['release'], kit['arch'])

    #check if this kit is already installed - by name, version, release and arch
    if checkKitInstalled02(koinst, db, kit['name'], kit['version'], kit['release'], kitinfo[3]):
            raise KitAlreadyInstalledError, \
                    "Cannot install kit '%s-%s-%s-%s' due to a conflicting kit already installed." % \
                    (kit['name'], kit['version'], kit['release'], kit['arch'])

    # populate the kit DB table with info
    newkit = db.Kits(rname=kit['name'], rdesc=kit['description'],
                     version=kit['version'], release=kit['release'], arch=kit['arch'],
                     removable=kit['removable'])
    newkit.save()

    db.flush()
    kl.debug('Addkit kid: %s', newkit.kid)

    # copy the RPMS
    repodir = koinst.kits_dir / str(newkit.kid)
    if not repodir.exists():
        repodir.makedirs()

    srcP = subprocess.Popen('tar cf - *.rpm', cwd=kitpath,
                            shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    dstP = subprocess.Popen('tar xf -',
                            cwd=repodir, shell=True, stdin=srcP.stdout,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dstP.communicate()

    # handle the kitinfo file, docs, and plugins
    kitrpm = kitinfo[3]
    kitrpm.extract(repodir)

    installPlugins(koinst, repodir, str(newkit.kid))
    installDocs(koinst, newkit)

    # check/populate component table
    try:
        updated_ngs = koinst.updateComponents(newkit, kitinfo[2])
    except ComponentAlreadyInstalledError, msg:
        # updateComponents encountered an error, remove kit from DB
        newkit.removable = True
        newkit.flush()
        koinst.deleteKit(del_name=kit['name'], del_id=newkit.kid)
        raise ComponentAlreadyInstalledError, msg
            
    return newkit.kid,updated_ngs


def checkKitInstalled02(koinst, db, kitname, kitver, kitrel, kitrpm):
    """
    Returns True if specified kit is already in the DB, False otherwise.
    """
    matches = db.Kits.select_by(rname=kitname)
    for m in matches:
        m_api = koinst.getKitApi(m.kid)
        if m_api == '0.1':
            return True
        if m_api == '0.2' and m.version == kitver and str(m.release) == kitrel:
            new_comps = koinst.getKitRPMInfo(kitrpm)[1]
            m_comps = processKitInfo(koinst.kits_dir / str(m.kid) / 'kitinfo')[1]
            for m in m_comps:
                for n in new_comps:
                    if hasMatchingOS(m, n):
                        return True
    return False


def hasMatchingOS(comp1, comp2):
    for os1 in comp1['os']:
        for os2 in comp2['os']:
            if os1['name'] == os2['name'] and \
               os1['major'] == os2['major'] and \
               (os1['minor'] == os2['minor'] or os1['minor'] == '*') and \
               (os1['arch'] == os2['arch'] or os1['arch'] == '*'):
                return True
    return False


def installPlugins(koinst, kitdir, kid):
    """
    Install kit plugins from a kit directory into the central plugin directory.
    """
    kl.debug('Installing kit plugins. Looking for plugins in this kit.')
    plugin_dir = kitdir / 'plugins'
    if not plugin_dir.exists():
        kl.debug('Plugins not found, finishing...')
        return
    for provider in [x.basename() for x in plugin_dir.dirs()]:
        kl.debug('Found %s plugins...' % provider)
        for plugin in [x.basename() for x in (plugin_dir / provider).files()]:
            proposed_plugin = koinst.kusu_root / 'lib' / 'plugins' / provider / plugin
            kl.debug('Checking if system already has %s' % proposed_plugin)
            if proposed_plugin.exists() or proposed_plugin.islink():
                kl.debug('Yes. Not creating symlink.')
            else:
                # temporary set the kitops prefix to '/' to reflect final destination.
                prefix = koinst.prefix
                koinst.setPrefix('/')
                actual_plugin = koinst.kits_dir / kid / 'plugins' / provider / plugin
                koinst.setPrefix(prefix)
                # original kitops prefix restored.
                kl.debug('No. Creating symlink to %s from %s' % (actual_plugin, proposed_plugin))
                if not proposed_plugin.dirname().exists():
                    proposed_plugin.dirname().makedirs()
                actual_plugin.symlink(proposed_plugin)


def installDocs(koinst, kit):
    """
    Install kit docs from a kit directory into the central docs directory.
    """
    kl.debug('Installing kit documentation. Looking for docs in this kit.')
    src_dir = koinst.kits_dir / str(kit.kid) / 'www'
    if not (src_dir.exists() or src_dir.islink()):
        kl.debug('kit %s does not have any documentation in %s' % \
                 (kit.rname, src_dir))
        return
    dest_dir = koinst.docs_dir / kit.rname / str(kit.version) / str(kit.release)
    kl.debug('Checking if proposed directory %s already exists.' % dest_dir)
    if dest_dir.exists() or dest_dir.islink():
        kl.debug('Proposed directory exists. Nothing left to do.')
        return
    else:
        # temporary set the kitops prefix to '/' to reflect final destination.
        prefix = koinst.prefix
        koinst.setPrefix('/')
        src_dir = koinst.kits_dir / str(kit.kid) / 'www'
        koinst.setPrefix(prefix)
        # original kitops prefix restored.
        kl.debug('No. Creating symlink to %s from %s' % (src_dir, dest_dir))
 
        if not dest_dir.dirname().exists():
            dest_dir.dirname().makedirs()
        src_dir.symlink(dest_dir)


def addkit02InstallerRules(koinst, db, kitinfo):
    kit = kitinfo[1]
    matches = db.Kits.select_by(rname=kit['name'])
    if matches:
        raise KitAlreadyInstalledError
    return addkit02(koinst, db, kitinfo)

def addkit03(koinst, db, kitinfo):
    """Add kit v0.3 strategy is same as add kit v0.2 strategy."""
    return addkit02(koinst, db, kitinfo)

AddKitStrategy = { '0.1': addkit01,
                   '0.2': addkit02,
                   '0.2-installer': addkit02InstallerRules,
                   '0.3': addkit03}
