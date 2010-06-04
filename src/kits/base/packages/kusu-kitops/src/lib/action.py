#!/usr/bin/env python
#
# $Id$
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#

import os
import sys
import types
import rpm
from sets import Set
import atexit

from kusu.util.errors import KitNotInstalledError, UpgradeKitError, UpgradeKitAbort
from kusu.util.lock import KusuProcessRegistry, KusuGlobalLock
from kusu.util.kits import matchComponentsToOS, compareVersion, SUPPORTED_KIT_APIS
from kusu.kitops.addkit_strategies import AddKitStrategy
from kusu.kitops.deletekit_strategies import DeleteKitStrategy
from kusu.repoman.repofactory import RepoFactory
from kusu.cfms import PackBuilder
from kusu.core.app import KusuApp

import kusu.util.log as kusulog
kl = kusulog.getKusuLog('kitops')

try:
    import subprocess
except ImportError:
    from popen5 import subprocess
from path import path


class KitopsAction(object):
    """Head of class hierarchy implementing actions on kits.

       Descendants of this class implement actions such as adding, updating or
       removing kits."""

    def __init__(self, db, koinst):
        """Create a KitopsAction instance.

           koinst is an instance of KitOps"""

        super(KitopsAction, self).__init__()

        self._db = db
        self.koinst = koinst

    def run(self, **kw):
        """Perform the action."""

        raise NotImplementedError

    def print_and_log(self, msg):
        """Prints msg to console as well as log with kusulogger."""
        print msg
        kl.info(msg)


class UpgradeAction(KitopsAction):

    def is_native_base_kit(self, kit):
        if kit.rname == 'base':
            installer_ng = self._db.NodeGroups.selectfirst_by(type='installer')
            return installer_ng.repo in kit.repos
        return False

    def validate_new_kit_for_upgrade(self, kit_tuple):
        """
        Checks whether the kit described by kit_tuple can be used in an upgrade.

        If for any reason the kit cannot be used in an upgrade, this method will
        raise an UpgradeKitError.
        """

        kit_api = kit_tuple[4]

        # Upgrading kits is supported from kit API 0.4 on.
        if kit_api not in SUPPORTED_KIT_APIS:
            msg = ("New kit API version '%s' is not supported. "
                   "Current version of kusu-kitops supports kit API versions up to '%s'.") \
                           % (kit_api, SUPPORTED_KIT_APIS[-1])
            kl.error(msg)
            raise UpgradeKitError, msg

        if -1 == compareVersion((kit_api, "0"), ("0.4", "0")):
            msg = "New kit API is %s. Upgrades only supported for kit API version 0.4 or newer." % kit_api
            kl.error(msg)
            raise UpgradeKitError, msg

    def validate_old_kit_for_upgrade(self, old_kit, oldest_upgradeable_version, oldest_upgradeable_release):
        """
        Checks whether old_kit can be upgraded.

        The check is performed based on the oldest_upgradeable_version and
        oldest_upgradeable_release specified in the new kit and passed into this
        method. If the kit is too old to be upgraded, this method raises an
        UpgradeKitError.
        The repositories to be upgraded with a new native base kit are also checked
        for staleness. If any repository containing the native base kit is stale,
        UpgradeKitError is raised.
        """

        # Check against oldest_upgradeable_version to determine whether a kit can be upgraded
        if -1 == compareVersion((old_kit.version, old_kit.release), (oldest_upgradeable_version, oldest_upgradeable_release)):
            msg = ("Unable to upgrade specified kit, version %(current_version)s-%(current_release)s, "
                   "oldest upgradeable version is %(oldest_version)s-%(oldest_release)s.") \
                    % {'current_version': old_kit.version,
                       'current_release': old_kit.release,
                       'oldest_version': oldest_upgradeable_version,
                       'oldest_release': oldest_upgradeable_release}
            kl.error(msg)
            raise UpgradeKitError, msg

        if self.is_native_base_kit(old_kit):
            for repo in old_kit.repos:
                repo_obj = RepoFactory(self._db).getRepo(repo.repoid)
                if repo_obj.isStale():
                    msg = "Unable to upgrade specified native base kit, %s-%s-%s, used in repository %s."\
                          "\nRepository is stale. Refresh the repository and rerun." % (old_kit.rname, old_kit.version,
                                                                                        old_kit.release, repo.reponame)
                    kl.error(msg)
                    raise UpgradeKitError, msg

    def _acquire_global_lock(self):
        process_registry = KusuProcessRegistry(os.getpid())
        if not process_registry.no_other_kusu_apps_running():
            msg = ("There are currently other kusu tools in use. For native base "
                   "kit upgrades, no other kusu tools should be running. Please "
                   "quit all running kusu tools first before trying the upgrade "
                   "again. Upgrade aborted.")
            kl.error(msg)
            raise UpgradeKitError, msg
        global_lock = KusuGlobalLock()
        global_lock.acquire()
        atexit.register(global_lock.release)

    def _get_old_kit(self, old_kit_id):
        old_kit_id = int(old_kit_id)
        old_kit = self._db.Kits.get(old_kit_id)
        if old_kit is None:
            msg = "Kit with id '%d' is not installed" % old_kit_id
            kl.error(msg)
            raise KitNotInstalledError, msg
        return old_kit

    def _get_possible_kits_to_upgrade(self, available_kits):
        possible_kits = []
        for kit in available_kits:
            # We have one level of indirection here...
            kit_api = kit[4]
            kitinfo = kit[1]
            # We only select kits that meet the following criteria:
            # [ ] have the same name (kit.rname)
            # [ ] have the same arch (kit.arch)
            # [ ] are newer than the kit being upgraded (kit.version/kit.release)
            if kitinfo['pkgname'] == 'kit-%s' % self.old_kit.rname \
                    and kitinfo['arch'] == self.old_kit.arch \
                    and -1 == compareVersion((self.old_kit.version, self.old_kit.release),
                                             (kitinfo['version'], kitinfo['release'])):
                possible_kits.append(kit)
        return possible_kits

    def _get_kit_long_name(self, kit):
        """
        Returns <name>-<version>-<release>-<arch> string.
        Pass in either a kitinfo dictionary or a Kits instance.
        """
        if isinstance(kit, dict):
            # kitinfo dictionary
            return "%s-%s-%s-%s" % (kit['name'],
                                    kit['version'],
                                    kit['release'],
                                    kit['arch'])
        else:
            # Assume this is an instance of Kits class
            return "%s-%s-%s-%s" % (kit.rname,
                                    kit.version,
                                    kit.release,
                                    kit.arch)

    def _select_one_kit(self, possible_kits):
        """
        From a list of possible kits, select one kit to use for the upgrade.
        """
        if len(possible_kits) == 1:
            return possible_kits[0]
        if self.suppress_questions:
            msg = ('Questions are suppressed for this upgrade action but user '
                   'is required to choose which kit to use for the upgrade.')
            kl.error(msg)
            raise UpgradeKitError, msg
        while True:
            for num_kits in enumerate(possible_kits):
                print '[%d]: %s' % (num_kits[0], self._get_kit_long_name(num_kits[1][1]))

            print 'Choose the kit to use for the upgrade or ENTER to quit: '
            res = sys.stdin.readline().strip()
            if not res:
                msg = 'No suitable kit selected for upgrade.'
                kl.info(msg)
                raise UpgradeKitAbort, msg
            try:
                return possible_kits[int(res)]
            except (ValueError, IndexError):
                print "ERROR: Invalid choice. Please try again.\n"

    def _verify_new_kit_has_compatible_components(self, kitinfo_components, existing_repos):
        """
        Verify that the components of a new kit are compatible with the existing repositories.
        """
        for repo in existing_repos:
            if not matchComponentsToOS(kitinfo_components, repo.getOS()):
                msg = "New kit does not have any components compatible with repo %s" % repo
                kl.error(msg)
                raise UpgradeKitError, msg

    def _get_user_confirmation(self, selected_kit):
        _old_kit = self._get_kit_long_name(self.old_kit)
        _selected_kit = self._get_kit_long_name(selected_kit[1])
        self.print_and_log("Upgrading from %s to %s." % (_old_kit, _selected_kit))
        if not self.suppress_questions:
            print 'Confirm [y/N]: '
            result = sys.stdin.readline().strip()
            if not result.lower() in ['y', 'yes']:
                msg = 'Upgrade action aborted.'
                kl.info(msg)
                raise UpgradeKitAbort, msg

    def _add_and_return_new_kit(self, selected_kit):
        # Add the new kit, and pull it from the DB
        kit_api = selected_kit[4]
        new_kit_id, updated_ngs = AddKitStrategy[kit_api](self.koinst, self._db,
                                                          selected_kit, update_action=True)
        self.print_and_log("Added new kit, ID is %s" % new_kit_id)
        return self._db.Kits.get(new_kit_id)

    def _reassociate_repos(self, associated_repos):
        if associated_repos:
            self.print_and_log("Associating repositories using the old kit with the new kit")
        for repo in associated_repos:
            # First, deassociate the old kit from the repo
            for i in xrange(len(repo.kits)):
                if self.old_kit.kid == repo.kits[i].kid:
                    repo.kits.pop(i)
                    break

            # Add the new kit
            repo.kits.append(self.new_kit)
            RepoFactory(self._db).getRepo(repo.repoid).markStale()
            repo.save_or_update()
            self._db.flush()

    def _update_repos(self, repos):
        self.print_and_log("Refreshing repositories: %s" % \
                           ", ".join([repo.reponame for repo in repos]))
        self.print_and_log("This may take a while to complete. Please do not "
                           "run any kusu commands until then.")

        for repo in repos:
            repo_obj = RepoFactory(self._db).getRepo(repo.repoid)
            try:
                self.print_and_log("\tRefreshing repo %s" % repo.reponame)
                repo_obj.refresh(repo.repoid)
            except Exception, e:
                kl.error("Upgrade failed. Unable to refresh repo %s. "
                         "Reason: %s." % (repo.reponame, e))
                sys.exit(1)
            else:
                self.print_and_log("\tFinished updating repo %s" % repo.reponame)

    def _reassociate_components_to_nodegroups(self, components_to_add):
        for old_component in self.old_kit.components:
            if old_component.nodegroups:
                self.print_and_log('Associating nodegroups using the old kit '
                                   'components with new kit components')
                break

        # We will need a mapping from new_kit.components to components_to_add
        component_mapping = {}
        for db_component in self.new_kit.components:
            for component in components_to_add:
                if db_component.cname == component['pkgname']:
                    component_mapping[db_component.cname] = component

        # Now we handle the nodegroup-component associations
        upgraded_nodegroups = Set()
        for new_component in self.new_kit.components:
            new_component_follows = component_mapping[new_component.cname]['follows']
            if not new_component_follows.startswith('component-'):
                new_component_follows = 'component-' + new_component_follows
            for old_component in self.old_kit.components:
                if old_component.cname == new_component.cname \
                        or new_component_follows == old_component.cname:
                    new_component.nodegroups = old_component.nodegroups
                    old_component.nodegroups = []
                    upgraded_nodegroups.update(new_component.nodegroups)

        return upgraded_nodegroups

    def _delete_old_kit(self):
        # For some reason, the in-memory representation of the DB is stale at
        # this point, so we need to re-load the old kit first before deleting
        # it.
        _old_kit_id = self.old_kit.kid
        self.old_kit = self._db.Kits.get(self.old_kit.kid)
        DeleteKitStrategy[self.koinst.getKitApi(self.old_kit.kid)](self.koinst, self._db,
                                                                   self.old_kit, update_action=True)
        self._db.flush()
        self.print_and_log("Removed old kit with ID %s" % _old_kit_id)

    def _remind_user_remaining_upgrade_steps(self):
        new_normal_kit = self.new_kit
        if new_normal_kit.repos:
            self.print_and_log("To complete the upgrade, please run the following commands:\n")
            for repo in new_normal_kit.repos:
                self.print_and_log("    kusu-repoman -u -r %s" % repo.reponame)

            nodegroups = Set([ng for comp in new_normal_kit.components for ng in comp.nodegroups])
            for ng in nodegroups:
                if ng.installtype == 'diskless' or ng.installtype == 'disked':
                    self.print_and_log("    kusu-buildimage -n %s" % ng.ngname)

            dpack_nodegroups = Set([ng for comp in new_normal_kit.components if comp.driverpacks for ng in comp.nodegroups])
            for ng in dpack_nodegroups:
                if ng.installtype == 'package':
                    self.print_and_log("    kusu-driverpatch nodegroup id %d" % ng.ngid)

            if nodegroups:
                self.print_and_log("    kusu-cfmsync -f -p -u\n")

    def _synchronize_nodegroups(self):
        self.print_and_log("Syncing nodegroups")

        # Use a dummy KusuApp instance for helper functions
        temp_app = KusuApp()

        # Initialize and prepare consolidated sync
        pb = PackBuilder(temp_app.errorMessage, temp_app.stdoutMessage)
        pb.consolidatedSync(action_type=11, ngname=None, ngid=0)

        # Re-initialize to get updated db state and signal for nodes to sync
        pb = PackBuilder(temp_app.errorMessage, temp_app.stdoutMessage)
        pb.signalUpdate(11, None)

    def _build_images_and_patch_drivers(self, nodegroups):
        new_driverpack_comps = [comp for comp in self.new_kit.components if comp.driverpacks]
        for ng in nodegroups:
            ng_driverpacks = Set([comps for comp in ng.components if comp in new_driverpack_comps])

            if ng.installtype == 'diskless' or ng.installtype == 'disked':
                self.print_and_log("Building image for %s nodegroup: %s. " \
                                   % (ng.type, ng.ngname))
                self.print_and_log("This may take a while to complete. Please "
                                   "do not run any kusu commands until then.")
                retcode = subprocess.call(['kusu-buildimage', '-n', ng.ngname])
                if retcode:
                    self.print_and_log("Buildimage failed. Please run manually "
                                       "after the upgrade has completed.")
                else:
                    self.print_and_log("Buildimage ran successfully.")

            elif ng.installtype == 'package' and ng_driverpacks:
                self.print_and_log("Patching drivers for %s nodegroup: %s." \
                                   % (ng.type, ng.ngname))
                self.print_and_log("This may take a while to complete. Please "
                                   "do not run any kusu commands until then.")

                # Find boot directory
                try:
                   bootdir = self._db.AppGlobals.selectone_by(kname='PIXIE_ROOT').kvalue
                except:
                   bootdir = '/tftpboot/kusu'

                # Copy over pristine initrd
                bootdir = path(bootdir)
                src_initrd = bootdir / ng_initrd
                dst_initrd = bootdir / 'initrd.%s.%d.img' % (ng_installtype, ngid)
                try:
                    src_initrd.copyfile(dst_initrd)
                except:
                    self.print_and_log('Warning: Failed to copy pristine initrd '
                                       'for this nodegroup. This failure will likely '
                                       'result in unexpected behaviour.\n')

                # Run kusu-driverpatch
                retcode = subprocess.call(['kusu-driverpatch', 'nodegroup', 'id', str(ng.ngid)])
                if retcode:
                    self.print_and_log("Driverpatch failed. Please run manually "
                                       "after the upgrade has completed.")
                else:
                    self.print_and_log("Driverpatch ran successfully.")

    def _update_kusu_version(self, version):
        kusu_ver = self._db.AppGlobals.selectfirst_by(kname='KUSU_VERSION')
        kusu_ver.kvalue = version
        kusu_ver.save_or_update()
        self._db.flush()

    def _remind_user_add_on_base_kit_upgrades(self):
        base_kits = self._db.Kits.select_by(rname='base')
        compatability_kits = ', '.join(['base-%s-%s kit id: %s' % (x.version, x.release, x.kid)
                                       for x in base_kits if x.kid != self.new_kit.kid])
        if compatability_kits:
            print "Please update the following compatability kits to the same version as the native " \
            "base kit (%s-%s): %s" % (self.new_kit.version, self.new_kit.release, compatability_kits)
            

    def run(self, **kw):
        """Perform the action."""

        self.old_kit = self._get_old_kit(kw.pop('old_kit_id'))
        possible_kits = self._get_possible_kits_to_upgrade(kw.pop('kits', []))
        self.suppress_questions = kw.pop('suppress_questions', False)

        if not possible_kits:
            msg = 'No suitable kits available for upgrade'
            kl.error(msg)
            raise UpgradeKitError, msg

        selected_kit = self._select_one_kit(possible_kits)
        components_to_add = selected_kit[2]

        # Verify both kits can be used in an upgrade.
        self.validate_new_kit_for_upgrade(selected_kit)
        self.validate_old_kit_for_upgrade(self.old_kit,
                                          selected_kit[1].get('oldest_upgradeable_version', ''),
                                          selected_kit[1].get('oldest_upgradeable_release', ''))

        # Get the list of repos the old kit is associated with. We will need to
        # associate the new kit with these repos.
        associated_repos = self.old_kit.repos

        self._verify_new_kit_has_compatible_components(components_to_add, associated_repos)

        self._get_user_confirmation(selected_kit)

        if self.is_native_base_kit(self.old_kit):
            self._acquire_global_lock()

        self.new_kit = self._add_and_return_new_kit(selected_kit)

        self._reassociate_repos(associated_repos)
        upgraded_nodegroups = self._reassociate_components_to_nodegroups(components_to_add)

        self._delete_old_kit()

        if self.is_native_base_kit(self.new_kit):
            self._update_repos(associated_repos)
            self._synchronize_nodegroups()
            self._build_images_and_patch_drivers(upgraded_nodegroups)
            self._update_kusu_version(self.new_kit.version)
            self._remind_user_add_on_base_kit_upgrades()
        else:
            self._remind_user_remaining_upgrade_steps()

