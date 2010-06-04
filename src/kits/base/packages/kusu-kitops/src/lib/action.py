#!/usr/bin/env python
#
# $Id$
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#

import sys
import types
import rpm
from kusu.util.errors import KitNotInstalledError, UpdateKitError
from kusu.util.kits import matchComponentsToOS, compareVersion, SUPPORTED_KIT_APIS
from kusu.kitops.addkit_strategies import AddKitStrategy
from kusu.kitops.deletekit_strategies import DeleteKitStrategy
from kusu.repoman.repofactory import RepoFactory

import kusu.util.log as kusulog
kl = kusulog.getKusuLog('kitops')

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

class UpdateAction(KitopsAction):

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
            # [ ] are newer than the kit being updated (kit.version/kit.release)
            if kitinfo['pkgname'] == 'kit-%s' % self.old_kit.rname \
                    and kitinfo['arch'] == self.old_kit.arch \
                    and -1 == compareVersion((self.old_kit.version, self.old_kit.release),
                                             (kitinfo['version'], kitinfo['release'])):
                possible_kits.append(kit)
        return possible_kits

    def _verify_new_kit_has_compatible_components(self, associated_repos):
        for repo in associated_repos:
            if not matchComponentsToOS(components_to_add, repo.getOS()):
                msg = "New kit does not have any components compatible with repo %s" % repo
                kl.error(msg)
                raise UpdateKitError, msg

    def _add_and_return_new_kit(self, selected_kit):
        # Add the new kit, and pull it from the DB
        kit_api = selected_kit[4]
        new_kit_id, updated_ngs = AddKitStrategy[kit_api](self.koinst, self._db,
                                                          selected_kit, update_action=True)
        return self._db.Kits.get(new_kit_id)

    def _reassociate_repos(self, associated_repos):
        for repo in associated_repos:
            # First, deassociate the old kit from the repo
            for i in xrange(len(repo.kits)):
                if self.old_kit.kid == repo.kits[i].kid:
                    repo.kits.pop(i)
                    break

            # Add the new kit
            repo.kits.append(self.new_kit)
            RepoFactory(self._db).getRepo(repo.repoid).markStale()
            repo.save()
            self._db.flush()

    def _reassociate_components_to_nodegroups(self, components_to_add):
        # We will need a mapping from new_kit.components to components_to_add
        component_mapping = {}
        for db_component in self.new_kit.components:
            for component in components_to_add:
                if db_component.cname == component['pkgname']:
                    component_mapping[db_component.cname] = component

        # Now we handle the nodegroup-component associations
        for new_component in self.new_kit.components:
            new_component_follows = component_mapping[new_component.cname]['follows']
            if not new_component_follows.startswith('component-'):
                new_component_follows = 'component-' + new_component_follows
            for old_component in self.old_kit.components:
                if old_component.cname == new_component.cname \
                        or new_component_follows == old_component.cname:
                    new_component.nodegroups = old_component.nodegroups
                    old_component.nodegroups = []

    def _delete_old_kit(self):
        # For some reason, the in-memory representation of the DB is stale at
        # this point, so we need to re-load the old kit first before deleting
        # it.
        self.old_kit = self._db.Kits.get(self.old_kit.kid)
        DeleteKitStrategy[self.koinst.getKitApi(self.old_kit.kid)](self.koinst, self._db,
                                                                   self.old_kit, update_action=True)
        self._db.flush()

    def _remind_user_remaining_upgrade_steps(self):
        new_normal_kit = self.new_kit
        if new_normal_kit.repos:
            print "To complete the upgrade, please run the following commands:\n"
            for repo in new_normal_kit.repos:
                print "    kusu-repoman -u -r %s" % repo.reponame
            for component in new_normal_kit.components:
                if component.nodegroups:
                    print "    kusu-cfmsync -f -p -u\n"
                    break

    def _select_one_kit(self, possible_kits):
        """
        From a list of possible kits, select one kit to use for the upgrade.
        """
        if len(possible_kits) == 1:
            return possible_kits[0]
        if self.suppress_questions:
            msg = ('Option --suppress-questions specified but user '
                   'is required to choose which kit to use for the upgrade.')
            kl.error(msg)
            raise UpdateKitError, msg
        while True:
            for num_kits in enumerate(possible_kits):
                print '[%d]: %s-%s-%s-%s' % (num_kits[0], num_kits[1][1]['name'],
                                             num_kits[1][1]['version'],
                                             num_kits[1][1]['release'],
                                             num_kits[1][1]['arch'])

            print 'Choose the kit to use for the upgrade or ENTER to quit: '
            res = sys.stdin.readline().strip()
            if not res:
                return None
            try:
                return possible_kits[int(res)]
            except (ValueError, IndexError):
                print "ERROR: Invalid choice. Please try again.\n"

    def run(self, **kw):
        """Perform the action."""

        self.old_kit = self._get_old_kit(kw.pop('old_kit_id'))
        possible_kits = self._get_possible_kits_to_upgrade(kw.pop('kits', []))
        self.suppress_questions = kw.pop('suppress_questions', False)

        if possible_kits:
            selected_kit = self._select_one_kit(possible_kits)
            if not selected_kit:
                msg = 'No suitable kit selected for upgrade'
                kl.error(msg)
                raise UpdateKitError, msg
            components_to_add = selected_kit[2]
        else:
            msg = 'No suitable kits available for upgrade'
            kl.error(msg)
            raise UpdateKitError, msg

        # Verify both kits can be used in an upgrade.
        validate_new_kit_for_upgrade(selected_kit)
        validate_old_kit_for_upgrade(self.old_kit,
                                     selected_kit[1].get('oldest_upgradeable_version', ''),
                                     selected_kit[1].get('oldest_upgradeable_release', ''))

        # Get the list of repos the old kit is associated with. We will need to
        # associate the new kit with these repos.
        associated_repos = self.old_kit.repos

        self._verify_new_kit_has_compatible_components(associated_repos)

        self.new_kit = self._add_and_return_new_kit(selected_kit)

        self._reassociate_repos(associated_repos)
        self._reassociate_components_to_nodegroups(components_to_add)

        self._delete_old_kit()

        if not self.new_kit.rname == 'base':
            self._remind_user_remaining_upgrade_steps()

        # TODO:
        # ...
        # Obtain user confirmation

def validate_new_kit_for_upgrade(kit_tuple):
    """
    Checks whether the kit described by kit_tuple can be used in an upgrade.

    If for any reason the kit cannot be used in an upgrade, this method will
    raise an UpdateKitError.
    """

    kit_api = kit_tuple[4]

    # Upgrading kits is supported from kit API 0.4 on.
    if kit_api not in SUPPORTED_KIT_APIS:
        msg = ("New kit API version '%s' is not supported. "
               "Current version of kusu-kitops supports kit API versions up to '%s'.") \
                       % (kit_api, SUPPORTED_KIT_APIS[-1])
        kl.error(msg)
        raise UpdateKitError, msg

    if -1 == compareVersion((kit_api, "0"), ("0.4", "0")):
        msg = "New kit API is %s. Upgrades only supported for kit API version 0.4 or newer." % kit_api
        kl.error(msg)
        raise UpdateKitError, msg

def validate_old_kit_for_upgrade(old_kit, oldest_upgradeable_version, oldest_upgradeable_release):
    """
    Checks whether old_kit can be upgraded.

    The check is performed based on the oldest_upgradeable_version and
    oldest_upgradeable_release specified in the new kit and passed into this
    method. If the kit is too old to be upgraded, this method raises an
    UpdateKitError.
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
        raise UpdateKitError, msg
