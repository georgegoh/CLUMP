import rpm

class UpdateAction(KitopsAction):
    def run(self, **kw):
        """Perform the action."""

        # Find the kit with the specified id. We assume there is only one.
        old_kit_id = kw.pop('old_kit_id')
        old_kit = self.koinst.findKits(None, old_kit_id, None, None)[0]

        # Determine which kit(s) in the supplied kit source (media, repo, etc)
        # can be updates.
        possible_kits = []
        available_kits = kw.pop('kits', [])
        for kit in available_kits:
            if kit.rname == old_kit.rname and kit.arch == old_kit.arch \
                    and isNewer(old_kit.version, old_kit.release, kit.version, kit.release):
                possible_kits.append(kit)

        # TODO:
        # Check kit API version; perhaps a method in the base class or even outside the KitopsAction hierarchy
        #   probably call addKitPrepare, at which point we will have access to all the kits
        # Find the new kit matching the old kit specified by id on the command line
        # Check min_version to determine whether a kit can be upgraded
        # Determine a list of repos the new kit can be added to
        # Determine whether an older version of the kit exists in these repos
        # Determine a list of nodegroups the older kit is associated with
        # ...
        # Obtain user confirmation
        # Run pre-section of kit upgrade plugin
        # Replace the old components with new ones accordingly
        # Run post section of kit upgrade plugin
        # Propmt user to run cfmsync --upgrade

def isNewer(old_ver, old_rel, new_ver, new_rel):
    """Compares old and new to determine whether new is newer.

    old_ver is the old version
    old_rel is the old release
    new_ver is the new version
    new_rel is the new release

    returns true if new is newer than old, false otherwise.
    """

    def toStr(a):
        if type(a) != types.StringType and a != None:
            a = str(a)
        return a

    old_ver = toStr(old_ver)
    old_rel = toStr(old_rel)

    new_ver = toStr(new_ver)
    new_rel = toStr(new_rel)

    return -1 == rpm.labelCompare(("0", old_ver, old_rel), ("0", new_ver, new_rel))
