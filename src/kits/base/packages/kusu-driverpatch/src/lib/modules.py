#!/usr/bin/env python
#
# $Id: modules.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
import os
from path import path
from kusu.core import database as db
from kusu.core.app import KusuApp
from kusu.util import tools as utiltools
from kusu.util import rpmtool, tools
from kusu.driverpatch import DriverPatchController
from kusu.util.errors import FileDoesNotExistError

class BaseInitrdModule:

    def __init__(self, db, initrdpath):

        self._ = KusuApp().langinit()
        self.stdoutMessage = KusuApp().stdoutMessage 
        self.db = db
        self.controller = DriverPatchController(self.db)

        self.tmpkmoddir = path(utiltools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
        self.tmppcidir = path(utiltools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
        self.tmpmoddir = path(utiltools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
        self.tmpdir = path(utiltools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
        self.tmpassetsdir = path(utiltools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
        self.initrdpath = initrdpath
 
    def printMsgExit(self, msg, exitcode=1):
        """ Print msg and exit. """
        self.stdoutMessage(msg)
        sys.stdout.write(os.linesep)
        sys.exit(exitcode)

    def updateInitrd(self, newinitrdpath, kernelrpm, kmodlist):
        ''' Update the initrd and return the path'''
        raise NotImplementedError

    def unpackInitrd(self):
        self.controller.unpackInitrdImage(self.initrdpath, self.tmpdir)
        return self.tmpdir

    def packInitrd(self, newinitrdpath):

        msg = self._('Packing the initrd..')
        print msg
        if newinitrdpath.exists(): newinitrdpath.remove()
        self.controller.packInitrdImage(newinitrdpath, self.tmpdir)
        msg = self._('Initrd image saved as /tftpboot/kusu/%(initrd)s' %
                    {'initrd':newinitrdpath.basename()})
        print msg
 
    def cleanup(self):
        if self.tmpkmoddir.exists(): self.tmpkmoddir.rmtree()
        if self.tmppcidir.exists(): self.tmppcidir.rmtree()
        if self.tmpmoddir.exists(): self.tmpmoddir.rmtree()
        if self.tmpdir.exists(): self.tmpdir.rmtree()
        if self.tmpassetsdir.exists(): self.tmpassetsdir.rmtree()

    def getKernelVersion(self, kernelrpm):
        return self.controller.getKernelVersion(kernelrpm.filename) # kernel version

    def getKernelModulesAssets(self):
        return self.controller.getKernelModulesAssets(self.tmpdir)

    def updateModulesAssets(self, origmodulesdep, origmodulesalias, kver):

        msg = self._('Generating updated modules.dep and modules.alias..')
        print msg

        try:
            self.controller.generateModulesAssets(self.tmpkmoddir, self.tmpassetsdir, kver)
        except FileDoesNotExistError:
            msg = self._('Error generating modules.dep!')
            self.printMsgExit(msg)

        modulesdep = self.tmpassetsdir / 'modules.dep'
        modulesalias = self.tmpassetsdir / 'modules.alias'

        if not modulesdep.exists(): 
            msg = self._('Error generating modules.dep!')
            self.printMsgExit(msg)
        
        li = self.controller.normalise_modules_dep(modulesdep)
 
        # write the updated modules.dep
        newmodulesdep = self.tmpassetsdir / 'modules.dep.new'
        newmodulesdep.write_lines(li)

        modulesdep.remove()
        newmodulesdep.copy(modulesdep)
        newmodulesdep.remove()
 
        origmodulesdep = path(self.tmpdir / origmodulesdep)
        origmodulesalias = path(self.tmpdir / origmodulesalias)
        
        if origmodulesdep.exists(): origmodulesdep.remove()
        if origmodulesalias.exists(): origmodulesalias.remove()
       
        modulesdep.copy(origmodulesdep.dirname())
        modulesalias.copy(origmodulesalias.dirname())

    def unpackKernelModules(self, moduleassets, kmodlist):
        # extract kernel modules from the driverpacks table

        modremovelist = []
        for pkg in kmodlist:
            msg = self._('Extracting kernel modules from package %(packagerpm)s..' %
                    {'packagerpm':pkg.filename})
            print msg

            #if cnt != 0: 
            dellist = []
	       
            tmpextractor = path(utiltools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
			
            self.controller.extractKernelModulesDir(pkg.filename,tmpextractor)

            for li in tmpextractor.walkfiles('*.ko'):
                dellist.append(os.path.basename(li))

            for delmod in dellist:
                item = self.tmpkmoddir.walkfiles(delmod)
                for li in item:
                    print "Replacing with vendor driver:  %s" % os.path.basename(li)
                    os.unlink(li)
            #cnt += 1

            # check if the package has a pci.updates
            # FIXME: currently only handling pci.updates! we are missing the support for pcitable types of updates.
            if self.controller.hasPciUpdates(pkg.filename): 
                self.controller.extractPciUpdates(pkg.filename,self.tmppcidir)
                pciupdates = path(self.tmppcidir / 'pci.updates')
                if not pciupdates.exists():
                    msg = self._('Error extracting pci.updates from %(packagerpm)s' %
                                {'packagerpm':pkg.filename})
                    self.printMsgExit(msg)
                # get system pci.ids found in the initrd and patch it with the new pci.updates
                syspci = moduleassets['pci.ids']
                msg = self._('Patching pci.ids with pci.updates found in %(packagerpm)s...' %
                            {'packagerpm':pkg.filename})
                print msg
                self.controller.patchPciIds(pkg.filename,syspci,pciupdates)
                # remove old pci.updates
                if pciupdates.exists(): pciupdates.remove()

            # check if the packagerpm has a modules.remove file
            if self.controller.hasModulesRemove(pkg.filename):
                self.controller.extractModulesRemoveFile(pkg.filename,self.tmpmoddir)
                modfile = path(self.tmpmoddir / 'modules.remove')
                if modfile.exists():
                    _modlist = self.controller.getModulesRemoveList(modfile)
                    modremovelist.extend([l for l in _modlist if l not in modremovelist])
                if tmpmoddir.exists(): tmpmoddir.rmtree()

            
            self.controller.extractKernelModulesDir(pkg.filename,self.tmpkmoddir)

        # remove any modules listed in modremovelist
        for mod in modremovelist:
            _li = tmpkmoddir.walkfiles(mod)
            if _li:
                for _mod in _li: _mod.remove()
        

class Redhat5InitrdModule(BaseInitrdModule):
    def __init__(self, db, initrdpath):
        BaseInitrdModule.__init__(self, db, initrdpath)

    def updateInitrd(self, newinitrdpath, kernelrpm, kmodlist):

        self.unpackInitrd()

        oldmodulescgz = self.controller.getKernelModulesCgz(self.tmpdir)
        oldmodulescgz.remove()

        kver = self.getKernelVersion(kernelrpm)
        moduleassets = self.getKernelModulesAssets()
        self.unpackKernelModules(moduleassets, kmodlist)

        origmodulesdep = 'modules/modules.dep'
        origmodulesalias = 'modules/modules.alias'
        self.updateModulesAssets(origmodulesdep, origmodulesalias, kver)

        msg = self._('Packing kernel modules as modules archive..')
        print msg
        self.controller.convertKmodDirToModulesArchive(self.tmpkmoddir,oldmodulescgz, kernelrpm.getArch())

        self.packInitrd(newinitrdpath)


class SLES10InitrdModule(BaseInitrdModule):
    def __init__(self, db, initrdpath):
        BaseInitrdModule.__init__(self, db, initrdpath)

    def updateInitrd(self, newinitrdpath, kernelrpm, kmodlist):
      
        # sles initrd layout
        # uname -r: 2.6.16.60-0.33-default
        #
        # /modules -> lib/modules/2.6.16.60-override-default/initrd
        # /lib/modules/2.6.16.60-0.33-default
        # /lib/modules/2.6.16.60-override-default/initrd
        #
        # /lib/modules/2.6.16.60-0.33-default, modules.* files
        # /lib/modules/2.6.16.60-0.33-default/updates -> ../2.6.16.60-override-default
        #
        # /lib/modules/2.6.16.60-override-default/initrd, ko files 
        
        pkg_ver = kernelrpm.version
        pkg_rel = kernelrpm.release
         
        self.unpackInitrd()
        kver = self.getKernelVersion(kernelrpm)

        for p in (self.tmpdir / 'lib' / 'modules').listdir():
            if (p / 'modules.dep').exists():
                p.move(self.tmpdir / 'lib' / 'modules' / '%s-default' % kver)  

            if (p / 'initrd').exists():
                p.move(self.tmpdir / 'lib'/ 'modules' / '%s-override-default' % pkg_ver)
       
        if (self.tmpdir / 'modules').islink(): (self.tmpdir / 'modules').remove()
        path('lib/modules/%s-override-default/initrd' % pkg_ver).symlink(self.tmpdir / 'modules')

        updatesdir = path(self.tmpdir / 'lib' / 'modules' / '%s-default' / 'updates' % kver)
        if (updatesdir).islink(): updatesdir.remove()
        path('../%s-override-default' % pkg_ver).symlink(updatesdir)
            
        moduleassets = self.getKernelModulesAssets()
        self.unpackKernelModules(moduleassets, kmodlist)
   
        origmodulesdep = 'lib/modules/%s-default/modules.dep' % kver
        origmodulesalias = 'lib/modules/%s-default/modules.alias' % kver
        self.updateModulesAssets(origmodulesdep, origmodulesalias, '%s-default' % kver)

        self.updateModulesInInitrd(self.tmpkmoddir, self.tmpdir, '%s-override-default' % pkg_ver)
        self.packInitrd(newinitrdpath)

    def updateModulesInInitrd(self, kmoddir, initrdpath, kver):

        destPath = initrdpath / 'lib' / 'modules' / kver / 'initrd'
        kofiles = [ko for ko in kmoddir.walkfiles('*.ko*')]
        for ko in kofiles:
            if (destPath / ko.basename()).exists():
                (destPath / ko.basename()).remove()
            ko.copy(destPath)
                
class OpenSUSE103InitrdModule(BaseInitrdModule):
    def __init__(self, db, initrdpath):
        BaseInitrdModule.__init__(self, db, initrdpath)

    def updateInitrd(self, newinitrdpath, kernelrpm, kmodlist):
      
        # opensuse 10.3 initrd layout
        # uname -r: 2.6.22.5-31-default
        #
        # /modules -> lib/modules/2.6.22.5-31-default/initrd
        # /lib/modules/2.6.22.5-31-default
        #
        # /lib/modules/2.6.22.5-31-default/ modules.* files
        # /lib/modules/2.6.22.5-31-default/initrd ko.* files
        
        pkg_ver = kernelrpm.version
        pkg_rel = kernelrpm.release
        
        self.unpackInitrd()
        kver = self.getKernelVersion(kernelrpm)

        for p in (self.tmpdir / 'lib' / 'modules').listdir():
            if (p / 'modules.dep').exists():
                p.move(self.tmpdir / 'lib' / 'modules' / '%s-default' % kver)  

        if (self.tmpdir / 'modules').islink(): (self.tmpdir / 'modules').remove()
        path('lib/modules/%s-default/initrd' % kver).symlink(self.tmpdir / 'modules')

        moduleassets = self.getKernelModulesAssets()
        self.unpackKernelModules(moduleassets, kmodlist)
   
        origmodulesdep = 'lib/modules/%s-default/modules.dep' % kver
        origmodulesalias = 'lib/modules/%s-default/modules.alias' % kver
        self.updateModulesAssets(origmodulesdep, origmodulesalias, '%s-default' % kver)

        self.updateModulesInInitrd(self.tmpkmoddir, self.tmpdir, '%s-default' % kver)
        self.packInitrd(newinitrdpath)

    def updateModulesInInitrd(self, kmoddir, initrdpath, kver):

        destPath = initrdpath / 'lib' / 'modules' / kver / 'initrd'
        kofiles = [ko for ko in kmoddir.walkfiles('*.ko*')]
        for ko in kofiles:
            if (destPath / ko.basename()).exists():
                (destPath / ko.basename()).remove()
            ko.copy(destPath)
 
    def updateModulesAssets(self, origmodulesdep, origmodulesalias, kver):

        msg = self._('Generating updated modules.dep and modules.alias..')
        print msg

        try:
            self.controller.generateModulesAssets(self.tmpkmoddir, self.tmpassetsdir, kver)
        except FileDoesNotExistError:
            msg = self._('Error generating modules.dep!')
            self.printMsgExit(msg)

        modulesdep = self.tmpassetsdir / 'modules.dep'
        modulesalias = self.tmpassetsdir / 'modules.alias'

        if not modulesdep.exists(): 
            msg = self._('Error generating modules.dep!')
            self.printMsgExit(msg)
        
        li = self.normalise_modules_dep(kver, modulesdep)
 
        # write the updated modules.dep
        newmodulesdep = self.tmpassetsdir / 'modules.dep.new'
        newmodulesdep.write_lines(li)

        modulesdep.remove()
        newmodulesdep.copy(modulesdep)
        newmodulesdep.remove()
        
        origmodulesdep = path(self.tmpdir / origmodulesdep)
        origmodulesalias = path(self.tmpdir / origmodulesalias)
        
        if origmodulesdep.exists(): origmodulesdep.remove()
        if origmodulesalias.exists(): origmodulesalias.remove()
       
        modulesdep.copy(origmodulesdep.dirname())
        modulesalias.copy(origmodulesalias.dirname())
        
    def normalise_modules_dep(self, kver, f):
        """ Normalises the generated modules.dep to be like how the initrd prefers it and returns it as a list
        """
            
        modulepath = path('/lib/modules/%s/initrd/' % kver)
        f = path(f)
        if not f.exists(): raise FileDoesNotExistError, f

        li = [l for l in open(f).read().split(os.linesep) if l]

        modlist = []
        for l in li:
            t = l.split(':')
            entry = []
            e1 = modulepath / path(t[0]).basename()
            entry.append(e1)
            if len(t) > 1:
                li2 = t[1].split()
                for l2 in li2:
                    entry.append(modulepath / path(l2).basename())

            # construct modlist
            s = '%s: %s' % (entry[0], ' '.join(entry[1:])) 
            modlist.append(s)

        return modlist

