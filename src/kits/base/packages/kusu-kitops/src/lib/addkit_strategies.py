import subprocess
from path import path
from kusu.util import rpmtool
from kusu.util.errors import KitAlreadyInstalledError,ComponentAlreadyInstalledError

import kusu.util.log as kusulog
kl = kusulog.getKusuLog('kitops')

# We currently want to limit the extent of association
# to certain ngids and below. 
NG_ASSOC_THRESHOLD = 2
USE_NG_ASSOC_THRESHOLD = True

def addkit01(koinst, db, kitinfo):
    kitpath = path(kitinfo[0])
    kit = kitinfo[1]
    kitrpm = '%s-%s-%s.%s.rpm' % (kit['pkgname'], kit['version'],
                                  kit['release'], kit['arch'])

    #check if this kit is already installed - by name, version, release and arch
    if koinst.checkKitInstalled(kit['name'], kit['version'], kit['release'], kit['arch']):
        raise KitAlreadyInstalledError, \
                "Kit '%s-%s-%s-%s' already installed" % \
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

    # also copy the kitinfo file
    kifile = kitpath / 'kitinfo'
    if kifile.exists(): kifile.copy(repodir)

    
    # check/populate component table
    try:
        updated_ngtypes = koinst.updateComponents(newkit.kid, kitinfo[2])
    except ComponentAlreadyInstalledError, msg:
        # updateComponents encountered an error, remove kit from DB
        newkit.removable = True
        newkit.flush()
        koinst.deleteKit(kit['name'], kit['version'], kit['arch'])
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

    # RPM install successful, add kit to DB

    # handling driverpacks

    # get the handle on components
    components = kitinfo[2]
    # FIXME: Put a proper try/except here!

    for comp in components:
        if 'driverpacks' in comp:
            # there should be one and only one component with the pkgname we want
            _comp = koinst.__db.Components.select_by(cname=comp['pkgname'])[0]
            for _dpack in comp['driverpacks']:
                dpname = _dpack['name']
                dpdesc = _dpack['description']
                dpack = db.DriverPacks()
                dpack.dpname = dpname
                dpack.dpdesc = dpdesc
                _comp.driverpacks.append(dpack)

            db.flush()

    return newkit.kid

def addkit02(koinst, db, kitinfo):
    kitpath = path(kitinfo[0])
    kit = kitinfo[1]
    kitrpm = '%s-%s-%s.%s.rpm' % (kit['pkgname'], kit['version'],
                                  kit['release'], kit['arch'])

    #check if this kit is already installed - by name, version, release and arch
    if koinst.checkKitInstalled(kit['name'], kit['version'], kit['release'], kit['arch']):
            raise KitAlreadyInstalledError, \
                    "Kit '%s-%s-%s-%s' already installed" % \
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

    # check/populate component table
    try:
        updated_ngtypes = koinst.updateComponents(newkit.kid, kitinfo[2])
    except ComponentAlreadyInstalledError, msg:
        # updateComponents encountered an error, remove kit from DB
        newkit.removable = True
        newkit.flush()
        koinst.deleteKit(kit['name'], kit['version'], kit['arch'])
        raise ComponentAlreadyInstalledError, msg
            
    # get the handle on components
    components = kitinfo[2]
    # FIXME: Put a proper try/except here!

    for comp in components:
        # each component may have one or more rows in the DB,
        # since a component can now be defined for multiple OSes.
        _components = db.Components.select_by(cname=comp['pkgname'])
        if 'driverpacks' in comp:
            for _dpack in comp['driverpacks']:
                dpname = _dpack['name']
                dpdesc = _dpack['description']
                dpack = db.DriverPacks()
                dpack.dpname = dpname
                dpack.dpdesc = dpdesc
                for _comp in _components:
                    _comp.driverpacks.append(dpack)
            db.flush()

        # for all ngtypes listed in the component,
        # find the nodegroups of that type.
        for t in comp['ngtypes']:
            _ngs = db.NodeGroups.select_by(type=t)
            for _ng in _ngs:
                # We currently want to limit the extent of association
                # to certain ngids and below.
                if USE_NG_ASSOC_THRESHOLD and _ng.ngid < NG_ASSOC_THRESHOLD:
                    # for each of the component entries created by this component,
                    # create an association with the nodegroup if it doesn't already exist.
                    for _comp in _components:
                        assoc = db.NGHasComp.select_by(ngid=_ng.ngid, cid=_comp.cid)
                        if not assoc:
                            newrelation = db.NGHasComp(ngid=_ng.ngid, cid=_comp.cid)
                            newrelation.save()
                            newrelation.flush()

    return newkit.kid


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
            if not proposed_plugin.exists():
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


AddKitStrategy = { '0.1': addkit01,
                   '0.2': addkit02}
