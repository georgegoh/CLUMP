#!/usr/bin/env python
# $Id$
#
# Kusu kit-install - Easy install tool for kits
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See COPYING file for details.
#

from kusu.kitops.kitops import KitOps
from kusu.ngedit.ngedit import NodeGroup as NGEditNodeGroup
from kusu.util.cfm import runCfmMaintainerScripts
from kusu.repoman.tools import isRepoStale
from kusu.core.db import KusuDB

from kusu.core import database as sadb
from kusu.kitinstall.helper import *

from path import path
import sys
import subprocess

INSTALLTYPE_SKIP_LIST = ['unmanaged', 'multiboot']

class KitInstall(object):
    def __init__(self):
        engine = os.getenv('KUSU_DB_ENGINE', 'postgres')
        self.dbs = sadb.DB(driver=engine, db='kusudb', username='apache')

    def addKits(self, source):
        '''Adds kits present in source using kitops.

           Returns the list of added and pre-existing kit ids.'''

        # Add kits using kusu-kitops
        cmd_list = ['kusu-kitops', '-a', '-s', '-m', source]
        # TODO Add a switch to kusu-kitops to turn component auto-association on/off.
        #      Run kusu-kitops above with auto-associations turned off.
        #      Modify 'associateComps' method to not expect any kitops auto-associations.
 
        out, err, retcode = responsive_run(cmd_list)
        if retcode:
            sys.stderr.write('kusu-kitops exited with return code %d.\n' % retcode)

        # Lets find out which kits were added and which were already installed
        added = []
        existing = []

        # We look for IDs of kits in kusu-kitops output and error dumps
        for line in (out+err).splitlines():
            kit_list = None
            full_name = ''

            # Parsing assumes that output will remain sames as that from kusu-kitops ver 2.0-1 
            if line.startswith('Added kit'):
                kit_id = int(line.strip().split(' ')[-1])
                added.append(kit_id)

            elif line.strip().endswith('already installed.'):
                kit_id = int(line.strip().split('(id:')[1].split(')')[0].strip())
                existing.append(kit_id)

        return added, existing


    def addKitsToRepos(self, kit_ids, repos):
        '''Adds the list of kits to each repository.

           Returns a dict of Kits added to each repo and the list of altered or stale repos' names.'''

        repo_kits = {}
        altered_repos = []
        stale_repos = []
        for repo in repos:
            # Find the list of kits already added to the repo
            db_repo = self.dbs.Repos.selectone_by(reponame=repo)
            db_repo_kits = [kit.kid for kit in db_repo.kits]

            # Use kusu-repoman to add the kits if not already present
            added = []
            present = []
            for kit_id in kit_ids:
                try:
                    db_kit = self.dbs.Kits.selectone_by(kid=kit_id)
                except:
                    continue

                if kit_id in db_repo_kits: # Skip pre-existing kit 
                    print 'Kit %d: %s is present in Repo: %s' % (kit_id, db_kit.getLongName(), repo)
                    present.append(db_kit)
                    continue

                cmd_list = ['kusu-repoman', '-a', '-r', repo, '-i', str(kit_id)]
                out, err, retcode = responsive_run(cmd_list)
                if retcode:
                    sys.stderr.write('kusu-repoman exited with return code %d.\n' % retcode)

                # Check output to determine if kit was added properly
                if err.strip().endswith('is not compatible with repo: %s' % repo):
                    continue
                if out.strip().endswith('Remember to refresh with -u'):
                    added.append(db_kit)

            # Note: This is to get updated records through the secondary join mapper: Repos.kits
            # Not clear if this should be moved to database.py's expire method
            db_repo.expire()

            if added or present:
                repo_kits[repo] = (added, present)
            if added:
                altered_repos.append(repo)
            elif present and isRepoStale(self.dbs, db_repo.repoid):
                stale_repos.append(repo)

        return repo_kits, altered_repos + stale_repos


    def refreshRepos(self, repos):
        '''Refreshes the repositories and returns a list of refreshed repos.
        '''

        # Refresh repos
        refreshed_repos = []
        for repo in repos:
            retcode = subprocess.call(['kusu-repoman', '-u', '-r', repo])

            # Check exit code
            if retcode:
                sys.stderr.write('kusu-repoman exited with return code %d.\n' % retcode)
            else:
                refreshed_repos.append(repo)

        return refreshed_repos


    def getRepoNodegroups(self, repos):
        '''Returns a list of NodeGroups for each repository.
        '''

        repo_dict = {}
        for repo in repos:
            try:
                db_repo = self.dbs.Repos.selectone_by(reponame=repo)
            except:
                continue

            # Get nodegroups list for each repo. Skip nodegroup if installtype is in INSTALLTYPE_SKIP_LIST
            repo_ngs = [ng for ng in db_repo.nodegroups if ng.installtype not in INSTALLTYPE_SKIP_LIST]
            repo_dict[repo] = repo_ngs

        return repo_dict


    def associateComps(self, repo_ngs, repo_kits):
        '''Associates components with the matching nodegroups

           Returns database component objects associated for each nodegroup'''

        ng_comps = {}
        for repo in repo_kits:
            new_kits, existing_kits = repo_kits[repo]
            sync_kits = new_kits + existing_kits
            # Determine the list of components to consider in the current execution
            repo_sync_comps = [comp for kit in sync_kits for comp in kit.components]

            for ng in repo_ngs[repo]:
                # Get components eligible for association and check against the current list
                eligible_comps = ng.getEligibleComponents(match_empty_ngtypes=False)
                relevant_comps = [comp for comp in eligible_comps if comp in repo_sync_comps]

                print 'Associating for nodegroup id: %d, nodegroup name: %s' % (ng.ngid, ng.ngname)
                # Find which components are already associated and which ones aren't
                existing_comps = [comp for comp in relevant_comps if comp in ng.components]
                matched_comps = [comp for comp in relevant_comps if comp not in existing_comps]

                if not existing_comps and not matched_comps:
                    print '\tnothing to do'
                    continue

                for comp in relevant_comps:
                    # For existing associations, print and skip
                    if comp in existing_comps:
                        print '\tdetected association for cid: %d, cname: %s' % (comp.cid, comp.cname)
                        continue

                    # Associate matched components with the nodegroup
                    nc = sadb.NGHasComp(ngid=ng.ngid, cid=comp.cid)
                    nc.save()
                    nc.flush()
                    self.dbs.expire_all()
                    print '\tassociated cid: %d, cname: %s' % (comp.cid, comp.cname)

                # Determine which components have been associated currently
                # Either auto-associated by kitops(new kits) or associated here (matched comps)
                new_kits_comps = [comp for kit in new_kits for comp in kit.components]
                comps_to_sync = [comp for comp in relevant_comps \
                                 if comp in new_kits_comps or comp in matched_comps]
                if comps_to_sync:
                    ng_comps[ng] = comps_to_sync

        return ng_comps


    def finalizeAndSyncChanges(self, ngs_comps):
        ''' Build images, patch the initrds and run the ngedit plugins for each nodegroup
        '''

        for ng in ngs_comps:
            print '\nFinalizing changes for nodegroup %s:' % ng.ngname

            # Build images for imaged nodegroups
            if ng.installtype == 'diskless' or ng.installtype == 'disked':
                print 'Build image for %s nodegroup %s:' % (ng.installtype, ng.ngname)
                self.runBuildimage(ng.ngname)
                print # new line

            # Build list of driver packs from all components
            dpack_comps = [dpack for comp in ngs_comps[ng] for dpack in comp.driverpacks]

            # Run kusu-driverpatch for packaged nodegroups
            if ng.installtype == 'package' and dpack_comps:
                print 'Running kusu-driverpatch nodegroup: %s' % ng.ngname
                self.runDriverpatch(ng.ngid, ng.initrd, ng.installtype)
                print # print new line

            # Run cfm maintainer scripts
            print 'Running CFM maintainer scripts'
            runCfmMaintainerScripts()

            # Run ngedit plugins
            print 'Running kusu-ngedit plugins for nodegroup: %s' % ng.ngname
            comp_ids = [comp.cid for comp in ngs_comps[ng]]
            self.runNgeditCompPlugins(ng.ngid, comp_ids)

            # Run cfmsync
            print 'Synchronizing nodegroup: %s' % ng.ngname
            self.syncNodegroup(ng.ngname)


    def runBuildimage(self, ngname):
        ''' Runs buildimage for the given nodegroup 
        '''

        # Run kusu-buildimage
        retcode = subprocess.call(['kusu-buildimage', '-n', ngname])
        if retcode:
            sys.stderr.write('kusu-buildimage exited with return code %d.\n' % retcode)


    def runDriverpatch(self, ngid, ng_initrd, ng_installtype):
        ''' Runs driverpatch for the given NodeGroup id
        '''

        # Find boot directory
        try:
            bootdir = self.dbs.AppGlobals.selectone_by(kname='PIXIE_ROOT').kvalue
        except:
            bootdir = '/tftpboot/kusu'

        # Copy over pristine initrd
        bootdir = path(bootdir)
        src_initrd = bootdir / ng_initrd
        dst_initrd = bootdir / 'initrd.%s.%d.img' % (ng_installtype, ngid)
        try:
            src_initrd.copyfile(dst_initrd)
        except:
            sys.stderr.write('Error copying pristine initrd for this nodegroup. ' \
                             'This failure will likely result in unexpected behaviour.\n')

        # Run kusu-driverpatch
        retcode = subprocess.call(['kusu-driverpatch', 'nodegroup', 'id', str(ngid)])
        if retcode:
            sys.stderr.write('kusu-driverpatch exited with return code %d.\n' % retcode)


    def runNgeditCompPlugins(self, ngid, comp_ids):
        '''Runs Ngedit 'add' plugins belonging to the given component ids
        '''

        # Set up and run plugins
        kdb = KusuDB()
        kdb.connect(user='apache', dbname='kusudb')
        ng = NGEditNodeGroup(ngid=ngid)
        ng._NodeGroup__handleCompPlug(kdb, comp_ids, 'add', self, None)

    def syncNodegroup(self, ngname):
        '''Synchronizes nodegroup using kusu-cfmsync
        '''

        # Run kusu-cfmsync
        cmd_list = ['kusu-cfmsync', '-f', '-p', '-u', '-n', ngname]
        out, err, retcode = responsive_run(cmd_list)
        if retcode:
            sys.stderr.write('kusu-cfmsync exited with return code %d.\n' % retcode)


    def runUsabilityScripts(self, kit_ids):
        '''Executes kit-install usability scripts for each kit
        '''

        # Check for kits' install root
        try:
            kits_root = self.dbs.AppGlobals.selectone_by(kname='DEPOT_KITS_ROOT').kvalue
        except:
            kits_root = '/depot/kits'

        status_list = []
        for kit_id in kit_ids:
            try:
                db_kit = self.dbs.Kits.selectone_by(kid=kit_id)
            except:
                continue

            # Look for script files under {DEPOT_KITS_ROOT}/<kid>/plugins/kit-install/
            scripts_path = path(kits_root) / str(kit_id) / 'plugins' / 'kit-install'
            scripts = scripts_path.glob('*')
            if scripts:
                print "\nRunning usability scripts for Kit %d: %s\n" % (kit_id, db_kit.getLongName())

            # Run the script files
            for script in scripts:
                retcode = subprocess.call([str(script)])

                if retcode:
                    status_list.append((script, 'failed'))
                    print 'Script %s exited with return code: %d\n' % (script.basename(), retcode)
                else:
                    status_list.append((script, 'completed'))
                    print 'Script %s ran successfully\n' % script.basename()

        if not status_list:
            print 'No usability scripts found in kits.'
        return status_list


    def deployKits(self, source, repos):
        '''Installs kits, adds to repos and associates with nodegroups.
        '''

        # Install kits from source
        print 'Installing kits from %s -' % source
        added_kits, existing_kits = self.addKits(source)

        kit_ids = added_kits + existing_kits
        if not kit_ids:
            exit_with_msg('Warning: kusu-kit-install terminated. No kits found in source provided.\n' \
                          'Make sure the source has at least one kit available.')

        # Add kits to repositories
        print '\nAdding kits to repositories -'
        repo_kits, stale_repos = self.addKitsToRepos(kit_ids, repos)

        if not repo_kits:
            exit_with_msg('Warning: kusu-kit-install terminated. No kits could be added to, or were found in the repositories.')

        # Refresh repositories to which kits were added
        if stale_repos:
            print '\nRefreshing repositories -'
            refreshed_repos = self.refreshRepos(stale_repos)
            bad_repos = [repo for repo in stale_repos if repo not in refreshed_repos]
            bad_repos_str = ', '.join(bad_repos)

            if refreshed_repos != stale_repos:
                exit_with_msg('Warning: kusu-kit-install terminated. Some repositories were not refreshed:\n\t%s' \
                              '\nRefresh these repositories manually using kusu-repoman.' % bad_repos_str)

        # Get nodegroup tuples for each repository
        repo_ngs = self.getRepoNodegroups(repos)

        # Associate components to matching nodegroups for each repository
        print '\nAssociating Components -'
        if not repo_ngs:
            exit_with_msg('Warning: kusu-kit-install terminated . No nodegroups found for the given repositories.\n' \
                          'To associate components, make sure nodegroups use the given repositories and rerun kusu-kit-install')

        ng_comps = self.associateComps(repo_ngs, repo_kits)

        # Finalize changes in the fashion of ngedit
        print '\nFinalizing changes made to nodegroups -'
        if not ng_comps:
            exit_with_msg('Warning: kusu-kit-install terminated. No nodegroups were altered.\n' \
                          'Run kusu-ngedit to associate components to nodegroups.')

        self.finalizeAndSyncChanges(ng_comps)

        # Run usability scripts for kit-install
        print '\nRunning kusu-kit-install usability scripts'
        self.runUsabilityScripts(kit_ids)

        print '\nFinished running kusu-kit-install.'

