#!/usr/bin/env python
#
# $Id$
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#

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
    def run(self, **kw):
        """Perform the action."""

        # Find the kit with the specified id. We assume there is only one.
        old_kit_id = int(kw.pop('old_kit_id'))
        old_kit = self._db.Kits.get(old_kit_id)

        if old_kit is None:
            msg = "Kit with id '%d' is not installed" % old_kit_id
            kl.error(msg)
            raise KitNotInstalledError, msg

        # Determine which kit(s) in the supplied kit source (media, repo, etc)
        # can be updates.
        possible_kits = []
        available_kits = kw.pop('kits', [])
        for kit in available_kits:
            # We have one level of indirection here...
            kit_api = kit[4]
            kitinfo = kit[1]
            # We only select kits that meet the following criteria:
            # [ ] have the same name (kit.rname)
            # [ ] have the same arch (kit.arch)
            # [ ] are newer than the kit being updated (kit.version/kit.release)
            if kitinfo['pkgname'] == 'kit-%s' % old_kit.rname and kitinfo['arch'] == old_kit.arch \
                    and -1 == compareVersion((old_kit.version, old_kit.release), (kitinfo['version'], kitinfo['release'])):
                possible_kits.append(kit)

        # TODO: Ask the user which new kit to use?
        if possible_kits:
            kit_to_add = possible_kits[0]
            components_to_add = kit_to_add[2]
        else:
            msg = 'No suitable kits available for upgrade'
            kl.error(msg)
            raise UpdateKitError, msg

        # Verify both kits can be used in an upgrade.
        validate_new_kit_for_upgrade(kit_to_add)
        validate_old_kit_for_upgrade(old_kit, kit_to_add[1].get('oldest_upgradeable_version', ''), kit_to_add[1].get('oldest_upgradeable_release', ''))

        # Get the list of repos the old kit is associated with. We will need to
        # associate the new kit with these repos.
        associated_repos = old_kit.repos

        # Check whether the new kit has compatible components.
        associated_repo_ids = []
        for repo in associated_repos:
            associated_repo_ids.append(repo.repoid)
            if not matchComponentsToOS(components_to_add, repo.getOS()):
                msg = "New kit does not have any components compatible with repo %s" % repo
                kl.error(msg)
                raise UpdateKitError, msg

        # Add the new kit, and pull it from the DB
        kit_api = kit_to_add[4]
        new_kit_id, updated_ngs = AddKitStrategy[kit_api](self.koinst, self._db, kit_to_add, update_action=True)
        new_kit = self._db.Kits.get(new_kit_id)

        # Let's re-associate repos
        for repo_id in associated_repo_ids:
            repo = self._db.Repos.get(repo_id)

            # First, deassociate the old kit from the repo
            for i in xrange(len(repo.kits)):
                if old_kit_id == repo.kits[i].kid:
                    repo.kits.pop(i)
                    break

            # Add the new kit
            repo.kits.append(new_kit)
            RepoFactory(self._db).getRepo(repo.repoid).markStale()
            repo.save()
            self._db.flush()

        # We will need a mapping from new_kit.components to components_to_add
        component_mapping = {}
        for db_component in new_kit.components:
            for component in components_to_add:
                if db_component.cname == component['pkgname']:
                    component_mapping[db_component.cname] = component

        # Now we handle the nodegroup-component associations
        for new_component in new_kit.components:
            for old_component in old_kit.components:
                if old_component.cname == new_component.cname \
                        or 'component-' + component_mapping[new_component.cname]['follows'] == old_component.cname:
                    new_component.nodegroups = old_component.nodegroups
                    old_component.nodegroups = []

        # For some reason, the in-memory representation of the DB is stale at
        # this point, so we need to re-load the old kit.
        old_kit = self._db.Kits.get(old_kit_id)
        DeleteKitStrategy[self.koinst.getKitApi(old_kit_id)](self.koinst, self._db, old_kit, update_action=True)
        self._db.flush()

        # TODO:
        # ...
        # Obtain user confirmation
        # Run pre-section of kit upgrade plugin
        # Replace the old components with new ones accordingly
        # Run post section of kit upgrade plugin
        # Propmt user to run cfmsync --upgrade

def validate_new_kit_for_upgrade(kit_tuple):
    """
    Checks whether the kit described by kit_tuple can be used in an upgrade.

    If for any reason the kit cannot be used in an upgrade, this method will
    raise an UpdateKitError.
    """

    kit_api = kit_tuple[4]

    # Upgrading kits is supported from kit API 0.4 on.
    if kit_api not in SUPPORTED_KIT_APIS:
        msg = "New kit API version is not supported."
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
