import sqlalchemy
import subprocess
from kusu.util.errors import DeleteKitsError

import kusu.util.log as kusulog
kl = kusulog.getKusuLog('kitops')

def deletekit01(koinst, db, kit):
    kl.info("Removing kit with kid '%s'" % kit.kid)

    try:
        # remove component info from DB
        for component in kit.components:
            for dpack in component.driverpacks:
                dpack.delete()
            component.delete()

        # remove kit DB info
        kit.delete()
    except sa.exceptions.SQLError, e:
        raise DeleteKitsError, [e]
 
    # uninstall kit RPM
    if not kit.isOS and not koinst.installer:
        cmds = ['/bin/rpm', '--quiet', '-e', '--nodeps',
                'kit-%s-%s' % (kit.rname, kit.version)]
        rpmP = subprocess.Popen(cmds,# shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        o, e = rpmP.communicate()
        kl.debug('Removing kit RPM stdout: %s, stderr: %s', o, e)
    elif koinst.installer:
        # remove any scripts
        koinst.removeRPMScripts(kit.rname, kit.version, kit.arch)

    # remove tftpboot contents
    if kit.isOS:
        p = koinst.pxeboot_dir / ('initrd-%s.img' % kit.longname)
        if p.exists(): p.remove()
        p = koinst.pxeboot_dir / ('kernel-%s' % kit.longname)
        if p.exists(): p.remove()
        if not koinst.pxeboot_dir.listdir():  # directory is empty
            koinst.pxeboot_dir.rmdir()

    # remove the RPMS kit contents
    kitdir = koinst.kits_dir / str(kit.kid)
    if kitdir.exists(): kitdir.rmtree()


def deletekit02(koinst, db, kit):
    kl.info("Removing kit with kid '%s'" % kit.kid)
    try:
        # remove component info from DB
        for component in kit.components:
            for dpack in component.driverpacks:
                dpack.delete()
            component.delete()

        # remove kit DB info
        kit.delete()
    except sqlalchemy.exceptions.SQLError, e:
        raise DeleteKitsError, [e]

    # uninstall plugins
    kitdir = koinst.kits_dir / str(kit.kid)
    uninstallPlugins(koinst.kusu_root, koinst.kits_dir, kitdir)

    # remove tftpboot contents
    if kit.isOS:
        p = koinst.pxeboot_dir / ('initrd-%s.img' % kit.longname)
        if p.exists(): p.remove()
        p = koinst.pxeboot_dir / ('kernel-%s' % kit.longname)
        if p.exists(): p.remove()
        if not koinst.pxeboot_dir.listdir():  # directory is empty
            koinst.pxeboot_dir.rmdir()

    # remove the RPMS kit contents
    del_path = koinst.kits_dir / str(kit.kid)
    if del_path.exists(): del_path.rmtree()


def uninstallPlugins(kusu_root, kits_root, kitdir):
    plugin_dir = kitdir / 'plugins'
    if not plugin_dir.exists():
        return
    for provider in [x.basename() for x in plugin_dir.dirs()]:
        for plugin in [x.basename() for x in (plugin_dir / provider).files()]:
            # construct the path of the plugin to remove.
            proposed_plugin = kusu_root / 'lib' / 'plugins' / provider / plugin
            plugin_exists = proposed_plugin.exists() or proposed_plugin.islink()
            if not plugin_exists:
                kl.debug('Plugin %s does not exist' % proposed_plugin)
                # if the path does not exist, then skip and go to next plugin.
                continue
            kl.debug('Plugin %s exists' % proposed_plugin)
            if proposed_plugin.realpath() == (plugin_dir / provider / plugin):
                # if the plugin symlinks to this kit, then it is a candidate for removal.
                if pluginUseCount(kits_root, provider, plugin) > 1:
                    # if other kits use this plugin, symlink to their copy of the
                    # plugin instead, since we are removing this kit.
                    resymlinkPlugin(kusu_root, kits_root, provider, plugin)
                else:
                    # else, no other kit uses this plugin, so remove it.
                    proposed_plugin.remove()


def pluginUseCount(kits_root, provider, plugin):
        count = 0
        for kit in kits_root.dirs():
            if (kit / 'plugins' / provider / plugin).exists():
                count += 1
        return count


def resymlinkPlugin(kusu_root, kits_root, provider, plugin):
    """
    Look for other kits which provide the same plugin and symlink
    to another kit.
    """
    if pluginUseCount(kits_root, provider, plugin) < 2:
        return
    link = kusu_root / 'lib' / 'plugins' / provider / plugin
    cur_target = link.realpath()
    for kit in kits_dir.dirs():
        new_target = kit / 'plugins' / provider / plugin
        if new_target.exists() and new_target != cur_target:
            link.remove()
            new_target.symlink(link)
            return


DeleteKitStrategy = { '0.1': deletekit01,
                      '0.2': deletekit02}
