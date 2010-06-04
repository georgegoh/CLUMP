#!/usr/bin/env python
# $Id$
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import atexit
from path import path
from kusu.core import database as db
from primitive.support import rpmtool
from kusu.repoman import tools as repotools
from kusu.driverpatch import DriverPatchController
from kusu.driverpatch.modulesfactory import InitrdModulesFactory
from kusu.util.errors import FileDoesNotExistError, RepoNotFoundError, DriverPatchActionError, \
                             InvalidArguments

SUPPORTED_KERNEL_ARCHES = ['i586','i686','x86_64']

class DriverPatch:
    def __init__(self, db, stdout, stderr):
        self.db = db
        self.stdoutMessage = stdout
        self.stderrMessage = stderr

        # an instance of the controller for managing the actions
        self.controller = DriverPatchController(self.db)

    def nodegroupAction(self, args):
        """ Handler for nodegroup action. args is a dict of supported key-value pairs for this action. """
        ngname = args.get('name','')
        ngid = args.get('id','')
        karch = args.get('arch','')
        kver = args.get('version','')
        kernelfile = args.get('kernel','')
        initrdfile = args.get('initrd','')
        assetsdir = args.get('assetsdir','')
        require_update = args.get('update', False)
        
        if not ngid and not ngname:
            raise InvalidArguments, 'Nodegroup Id or Name not provided.'

        if ngname:
            ngkey = 'name'
        elif ngid:
            ngkey = 'id'
            
        # get the ngname
        if ngkey == 'id':
            try:
                _ngid = long(ngid)
            except ValueError:
                msg = ('id should be a number!')
                raise InvalidArguments, msg
            
            _ng = self.db.NodeGroups.select_by(ngid=_ngid)
            if _ng:
                ng = _ng[0]
                ngname = ng.ngname
            else:
                msg = ('Nodegroup not found!')
                raise InvalidArguments, msg
    
        else:
            # validate the supplied ngname
            _ng = self.db.NodeGroups.select_by(ngname=ngname)
            if not _ng:
                msg = ('Nodegroup not found!')
                raise InvalidArguments, msg

            
        # get the available driverpacks
        try:
            dpacks = self.controller.getDriverPacks(id=ngid,name=ngname)
        except ValueError:
            msg = ('id should be a number!')
            raise InvalidArguments, msg
            
        if not dpacks:
            msg = ("No valid driverpacks found. Please ensure that the nodegroup's installtype is package-based.")
            raise DriverPatchActionError, msg
                    
        # get the correct dpacks
        #dprpms = [dpack.dpname for dpack in dpacks if dpack.dpname.find(karch) >-1]
        dprpms = [dpack.dpname for dpack in dpacks]

        if not dprpms:
            msg = ('No valid driverpacks found.')
            raise DriverPatchActionError, msg
        
        for dprpm in dprpms:
            msg = ('Found valid driverpack: %(dpname)s\n' %
                        {'dpname':dprpm})
            self.stdoutMessage(msg)
            
        # get the repoid for this nodegroup
        if not repotools.repoForNodeGroupExists(self.db,ngname):
            msg = ('No valid repo available for this nodegroup!')
            raise DriverPatchActionError, msg
            
        repoid = repotools.getRepoFromNodeGroup(self.db,ngname)
        repos = self.db.Repos.select_by(repoid=repoid)
        repo = repos[0].repository
        if not repo:
            msg = ('No valid repo available for this nodegroup!')
            raise DriverPatchActionError, msg
            
        msg = ('Looking in %(repository)s..\n' %
                    {'repository':repo})
        self.stdoutMessage(msg)
        
        # lets get the driverpacks packages
        pkglist = []
        for dprpm in dprpms:
            try:
                pkg = repotools.getPackageFilePath(self.db,repoid,dprpm)
                pkglist.append(pkg)
            except RepoNotFoundError:
                msg = ('No valid repo available for this nodegroup!')
                raise DriverPatchActionError, msg
            except FileDoesNotExistError:
                msg = ('%(pkgname)s not available in for the repo belong to this nodegroup! Skipping.\n' %
                            {'pkgname':dprpm})
                self.stdoutMessage(msg)
 
        for pkg in pkglist:
            msg = ('Found %(pkgname)s..\n' %
                        {'pkgname':pkg})
            self.stdoutMessage(msg)
        
        tftpbootdir = path('/tftpboot/kusu')
        if not tftpbootdir.exists():
            msg = ('/tftpboot/kusu not found! Aborting operation.')
            raise DriverPatchActionError, msg
        
        # get the kernel rpm
        li = []
        for pkg in pkglist:
            if self.controller.isKernelPackage(pkg):
                li.append(pkg)

        if not li:
            msg = ('Kernel rpm not found!')
            raise DriverPatchActionError, msg
            
        # remove the kernel rpms for the pkglist
        kmodlist = [rpmtool.RPM(str(pkg)) for pkg in pkglist if not pkg in li]
        
        # if there are more than one kernel rpms, get the highest one

        if len(li) > 1:
            krpms = [rpmtool.RPM(str(l)) for l in li]
            try:
                krpms.sort()
            except RPMComparisonError:
                msg = ('Different types of kernel packages found for this distro! This is unsupported!')
                raise DriverPatchActionError, msg
                
            kernelrpm = krpms[-1]   # last one is the highest
        else:
            kernelrpm = rpmtool.RPM(str(li[0]))

        msg = ('Using %(package)s as the kernel package.' %
                {'package':str(kernelrpm)})
                
        # add the select kernelrpm into the kernel modules list
        kmodlist.insert(0,kernelrpm)
        
        # get the current kernel/initrd for this nodegroup
        _ng = self.db.NodeGroups.select_by(ngname=ngname)

        # FIXME: Ensure the ngedit has not updated the kernel/initrd fields!
        ngkernel = _ng[0].kernel
        nginitrd = _ng[0].initrd
        
        # create a toplevel scratch directory
        # FIXME: Hardcoding for now
        if not path('/var/cache/kusu-driverpatch').exists(): path('/var/cache/kusu-driverpatch').mkdir()
        atexit.register(self.removeTempDir, '/var/cache/kusu-driverpatch')

        # get the existing initrd
        initrdpath = tftpbootdir / nginitrd
        if not initrdpath.exists():
            msg = ('Current initrd %(initrdpath)s not found! Aborting operation!' %
                        {'initrdpath':initrdpath})
            raise DriverPatchActionError, msg
            
        if not initrdfile:
            newinitrd = nginitrd
        else:
            newinitrd = initrdfile

        if not kernelfile:
            kernelfile = ngkernel

        os_name, os_version, os_minor, os_arch = repotools.getOS(self.db, repoid)

        if os_name in ['opensuse']:
            os_ver = '%s.%s' % (os_version, os_minor)
        else:
            os_ver = os_version

        moduleHandler = InitrdModulesFactory().getModuleHandler(os_name, os_ver)(self.db, initrdpath)
        newinitrdpath = tftpbootdir / newinitrd
        moduleHandler.updateInitrd(newinitrdpath, kernelrpm, kmodlist)

        msg = ('Extracting kernel image to /tftpboot/kusu..\n')
        self.stdoutMessage(msg)
        # expects kernelrpm filepath, not an instance of rpmtool.RPM
        kernelname = self.controller.copyKernel(kernelrpm.filename,tftpbootdir,kernelfile)
        msg = ('Kernel image saved as /tftpboot/kusu/%(kernelname)s\n' %
                    {'kernelname':kernelname})
        self.stdoutMessage(msg)
        
        # update the kernel/initrd entries for this nodegroup if required
        if require_update:
            msg = ('Updating kernel/initrd entries for this nodegroup.\n')
            self.stdoutMessage(msg)
            ngs = self.db.NodeGroups.select_by(ngname=ngname)
            ng = ngs[0]
            ng.kernel = kernelname
            ng.initrd = newinitrd
            ng.flush()
        
        moduleHandler.cleanup()

    def listAction(self, args):
        """ Handler for list action. args is a dict of supported key-value pairs for this action. """
        ngname = args.get('name','')
        ngid = args.get('id','')


        if not ngid and not ngname:
            raise InvalidArguments, 'Nodegroup Id or Name not provided.'
        
        if ngname:
            ngkey = 'name'
        elif ngid:
            ngkey = 'id'
            
        try:
            dpacks = self.controller.getDriverPacks(id=ngid,name=ngname)
        except ValueError:
            msg = ('id should be a number!')
            raise InvalidArguments, msg
            
            
        if dpacks:
            msg = ("Driverpacks belonging to nodegroup(s) matching '%(ngkey)s=%(ngval)s':\n" % 
                {'ngkey':ngkey,
                'ngval':ngid or ngname})
            self.stdoutMessage(msg)

            headers = ['name','description']
            max_lengths = []
            for x in xrange(len(headers)):
                max_lengths.append(len(headers[x]))
            
            dplines = []
            for dpack in dpacks:
                dpline = []
                dpline.append(dpack.dpname)
                dpline.append(dpack.dpdesc)
                
                # update maximum lengths
                for x in xrange(len(dpline)):
                    linelengths = [len(l) for l in dpline[x].split('\n')]
                    if max(linelengths) > max_lengths[x]:
                        max_lengths[x] = max(linelengths)

                dplines.append(dpline)
            
            self.printTable(headers, dplines, max_lengths)

    def printTable(self, titles, entries, widths):
        horline = '+'
        for width in widths:
            horline += '-' * (width + 2) + '+'
    
        self.stdoutMessage(horline+'\n')
    
        line = '|'
        for x in xrange(len(titles)):
            line += ' ' + titles[x].ljust(widths[x]) + ' |'
    
        self.stdoutMessage(line+'\n')
        self.stdoutMessage(horline+'\n')
    
        for entry in entries:
            newlines = True
            while newlines:
                newlines = False
    
                line = '|'
                for x in xrange(len(entry)):
                    newline = entry[x].find('\n')
                    if newline == -1:
                        thisentry = entry[x]
                        nextentry = ''
                    else:
                        newlines = True
                        thisentry = entry[x][:newline]
                        nextentry = entry[x][newline + 1:]
    
                    line += ' ' + thisentry.ljust(widths[x]) + ' |'
                    entry[x] = nextentry
    
                self.stdoutMessage(line+'\n')
    
        self.stdoutMessage(horline+'\n')
    
    def removeTempDir(self, directory):
        """Forcibly remove the directory"""
        if path(directory).exists():
            path(directory).rmtree()
    
