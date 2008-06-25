#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from path import path
from Cheetah.Template import Template
import tarfile
from random import choice
import string
import os
import pwd
from kusu.util.tools import cpio_copytree
from kusu.util.errors import FileDoesNotExistError, PackageAttributeNotDefined, UnsupportedScriptMode
from kusu.util.structure import Struct
from kusu.util import rpmtool
from kusu.util import compat

try:
    import subprocess 
except: 
    from popen5 import subprocess


SUPPORTED_TARFILES_EXT = ['.tgz','.tar.gz','.tbz2','.tar.bz2','.zip','.tar']
SUPPORTED_DISTROPKG_EXT = ['.src.rpm','.rpm','.srpm','.deb']

def genrandomstr(length=8):
    chars = string.letters + string.digits
    return ''.join([choice(chars) for i in range(length)])
    
def stripShebang(script):
    """ Strip the shebang and returns the script text.
    """
    li = open(script).readlines()
    lines = []
    if li[0].startswith('#!'):
        lines = li[1:]
    else:
        lines = li
        
    return ''.join(lines)
        
    
def derivePackageNVR(filenamestr):
    """ Tries to derive the name, version and release out of the filenamestr or
        returns tuple containing empty strings.
    """
    if not filenamestr: return ('','','')

    # let's just get the essentials
    EXTS = SUPPORTED_DISTROPKG_EXT + SUPPORTED_TARFILES_EXT

    li = [filenamestr.split(ext) for ext in EXTS if filenamestr.endswith(ext)]
    if not li: return ('','','')
    nvr = li[0][0]
    li = nvr.split('-')

    if len(li) > 2: return (li[0],li[1],''.join(li[2:]))
    if len(li) > 1: return (li[0],li[1],'')
    if len(li) == 1: return (li[0],'','')

    return ('','','')

def setupRPMMacrofile(buildprofile):
    """ Creates a proper .rpmmacros file for purposes of building kits. 
        If an existing .rpmmacros exists, it will be renamed and this
        function will return the old .rpmmacros file for safekeeping.
    """
    userhome = path(pwd.getpwuid(os.getuid())[5])
    rpmmacros = userhome / '.rpmmacros'
    rpmmacrosExists = False
    if rpmmacros.exists():
        rpmmacrosExists = True
        ext = genrandomstr()
        _oldrpmmacros = '.'.join([rpmmacros,ext])
        rpmmacros.rename(_oldrpmmacros)
        _oldrpmmacros = path(_oldrpmmacros)

    rpmtopdir = path(buildprofile.builddir) / 'packages'
    if not rpmtopdir.exists(): 
        rpmtopdir.mkdir()
        path(rpmtopdir / 'BUILD').mkdir()
        path(rpmtopdir / 'RPMS').mkdir()
    kusuroot = path(os.environ.get('KUSU_ROOT','/opt/kusu'))
    tmpldir = kusuroot / 'etc/buildkit-templates'
    rpmmacroTmpl = path(tmpldir / 'rpmmacros.tmpl')

    d = {}
    d['topdir'] = rpmtopdir
    d['tmppath'] = path(buildprofile.tmpdir)

    t = Template(file=str(rpmmacroTmpl),searchList=[d])
    f = open(rpmmacros,'w')
    f.write(str(t))

    if rpmmacrosExists and _oldrpmmacros.exists(): 
        return (True,_oldrpmmacros)
    else:
        return (False,None)

def prepareNS(packageprofile):
    """ Prepare a namespace dict for generating templates. """
    d = {}
    d['pkgname'] = packageprofile.name
    d['approot'] = packageprofile.installroot
    d['pkgversion'] = packageprofile.version
    d['pkgrelease'] = packageprofile.release
    if packageprofile.license:
        d['license'] = packageprofile.license
    if packageprofile.author:
        d['author'] = packageprofile.author
    if packageprofile.vendor:
        d['vendor'] = packageprofile.vendor
    if hasattr(packageprofile,'scripts'):
        d['prescript'] = packageprofile.scripts['prescript']
        d['preunscript'] = packageprofile.scripts['preunscript']
        d['postscript'] = packageprofile.scripts['postscript']
        d['postunscript'] = packageprofile.scripts['postunscript']
                            
    return d


def getPackageSpecTmpl(templatesdir):
    """ Gets the specfile template for package. """
    root = path(templatesdir)
    spectmpl = root.files('package.spec.tmpl')[0]
    
    return spectmpl
    
def getBuildKitTemplate(templatedir=None):
    """ Get the specfile for components. """
    if not templatedir:
        kusuroot = path(os.environ.get('KUSU_ROOT','/opt/kusu'))
        templatedir = kusuroot / 'etc/buildkit-templates'
    tmpldir = path(templatedir)
    _t = 'build.kit.tmpl'
    tmpl = tmpldir / _t

    if not tmpl.exists(): raise FileDoesNotExistError
    return tmpl    
    
    
def getTemplateSpec(templatetype, templatedir=None):
    """ Get the specfile for components. """
    if not templatedir:
        kusuroot = path(os.environ.get('KUSU_ROOT','/opt/kusu'))
        templatedir = kusuroot / 'etc/buildkit-templates'
    tmpldir = path(templatedir)
    _t = '%s.spec.tmpl' % templatetype
    tmpl = tmpldir / _t

    if not tmpl.exists(): raise FileDoesNotExistError
    return tmpl
    
def getScriptTemplate(scripttype, templatedir=None):
    """ Get the template for scripts. """
    if not templatedir:
        kusuroot = path(os.environ.get('KUSU_ROOT','/opt/kusu'))
        templatedir = kusuroot / 'etc/buildkit-templates'
    tmpldir = path(templatedir)
    _t = '00-%s-script.sh.tmpl' % scripttype
    tmpl = tmpldir / _t

    if not tmpl.exists(): raise FileDoesNotExistError
    return tmpl

def getDirName(p):
    """ Returns the unpacked directory name of a tarfile. """
    li = [ext for ext in SUPPORTED_TARFILES_EXT if ext in p]
    if li:
        return p.split(li[0])[0]

def unpackTarfile(filename, destroot=None):
    """ Convenience method to unpack tarfiles. """
    if not destroot:
        destroot = path.getcwd()
    else:
        destroot = path(destroot)

    pkg = tarfile.open(filename)
    for f in pkg:
        pkg.extract(f,destroot)


class BuildProfile(Struct):
    """ Profile used to store build site configuration. """
    
    def __init__(self, **kwargs):
        Struct.__init__(self,kwargs)

        kusuroot = path(os.environ.get('KUSU_ROOT','/opt/kusu'))
        tmpldir = kusuroot / 'etc/buildkit-templates'
        self.templatesdir = kwargs.get('templatesdir', tmpldir)

class PackageProfile(Struct):
    """ Package-specific profile used to build packages. The appropriate
        Wrapper object will need to be associated in order to provide
        functionality.
    """
    
    def __init__(self, wrapper, **kwargs):
        Struct.__init__(self)

        self.wrapper = wrapper
                    
        self.verbose = kwargs.get('verbose',False)
        self.srctype = kwargs.get('srctype','')
        self._name = kwargs.get('name','')
        self._version = kwargs.get('version','')
        self._release = kwargs.get('release','0')
        self.filename = kwargs.get('filename',None)
        self.installroot = kwargs.get('installroot',None)
        self.ostype = kwargs.get('ostype','')
        self.author = kwargs.get('author','')
        self.vendor = kwargs.get('vendor','')
        self.license = kwargs.get('license','')
        self.buildprofile = kwargs.get('buildprofile','')
        self.description = kwargs.get('description','')
        self.driverpack = kwargs.get('driverpack',False)
        self._queuecmds = []


    def setup(self):
        """ Preps the wrapper object with the attributes. This must be called before
            calling other operations.
        """
        self.builddir = path(self.buildprofile.builddir)
        self.srcdir = path(self.buildprofile.srcdir)
        self.pkgdir = path(self.buildprofile.pkgdir)
        self.tmpdir = path(self.buildprofile.tmpdir)
        self.templatesdir = path(self.buildprofile.templatesdir)

        if self.srctype == 'rpm':
            if not hasattr(self,'filename'): raise PackageAttributeNotDefined, 'filename'
            filename = self.srcdir / self.filename
            if not filename.exists(): raise FileDoesNotExistError, filename
            r = rpmtool.RPM(str(filename))
            self.name = r.getName()
            self.version = r.getVersion()
            self.release = r.getRelease()
            self.arch = r.getArch()
            if not self.description: self.description = r.description[:255]
            
        elif self.srctype in  ['srpm','rpm','binarydist','autotools']:
            # ensure that the name, version, release are defined.
            if not hasattr(self,'name'): raise PackageAttributeNotDefined, 'name'
            if not hasattr(self,'version'): raise PackageAttributeNotDefined, 'version'
            if not hasattr(self,'release'): raise PackageAttributeNotDefined, 'release'            

        if not self.srctype in ['srpm','rpm','distro']:
            
            filename = self.srcdir / self.filename
            self.fullname = getDirName(filename.basename())
            self.buildsrc = self.tmpdir / self.fullname
            
        # add the scripts attribute for those srctypes that
        # support them.
        if self.srctype in ['autotools', 'binarydist']:
            self.scripts = {}
            self.scripts['postscript'] = ''
            self.scripts['postunscript'] = ''
            self.scripts['preunscript'] = ''
            self.scripts['prescript'] = ''

        # expose the attributes to the wrapper object
        self.wrapper.update(Struct(self))
        self.wrapper.verbose=self.verbose
        
    def _processAddScripts(self):
        """ Process any queued commands.
        """
        for cmd in self._queuecmds:
            if len(cmd) > 1:
                func = cmd[0]
                args = cmd[1:]
            else:
                func = cmd[0]
                args = []
                
            func(*args)

    def verify(self):
        return self.wrapper.verify()

    def addScript(self, script, mode='post'):
        self._queuecmds.append((self.wrapper.addScript,script,mode))

    def cleanup(self):
        return self.wrapper.cleanup()

    def configure(self, **kwargs):
        """ Configuration stage for this class. """
        return self.wrapper.configure(**kwargs)

    def build(self, **kwargs):
        """ Build stage for this class. """
        return self.wrapper.build(**kwargs)

    def install(self, **kwargs):
        """ Installation stage for this class. """
        return self.wrapper.install(**kwargs)

    def deploy(self, pkgtype='rpm', verbose=False):
        """ Deploying stage. This includes packing into distro-specific packages (if needed).
        """
        return self.wrapper.deploy(pkgtype,verbose)

class PackageWrapper(Struct):
    """ Base class. PackageWrapper provides easy access to attributes and
        its methods deal with package operations such as verification, rpm 
        packaging and others.
    """
    
    verbose = False
    
    def __init__(self):
        """ Initializes the Struct class for easy access to attributes.
        """
        Struct.__init__(self)
        
    def verify(self):
        if not hasattr(self,'filename'): raise PackageAttributeNotDefined, 'filename'
        filename = self.srcdir / self.filename
        if not filename.exists(): raise FileDoesNotExistError, filename

    def cleanup(self):
        if not hasattr(self,'buildsrc'): return
        if self.buildsrc.exists(): self.buildsrc.rmtree()

    def configure(self, **kwargs):
        """ Configuration stage for this class. Override this to customize.
        """

        pass

    def build(self, **kwargs):
        """ Build stage for this class. Override this to customize.
        """

        pass      

    def install(self, **kwargs):
        """ Installation stage for this class. Override this to customize.
        """

        pass
        
    def addScript(self, script, mode='post'):
        pass

    def _packRPM(self, verbose=False):
        """ RPM handling stage for this class. This package type-specific 
            and has to be implemented.
        """
        raise NotImplementedError
        
    def _packDEB(self, verbose=False):
        """ DEB handling stage for this class. This package type-specific 
            and has to be implemented.
        """
        raise NotImplementedError

    def deploy(self, pkgtype='rpm', verbose=False):
        """ Deploying stage. """

        if pkgtype == 'rpm':
            return self._packRPM(verbose)
            
        elif pkgtype == 'deb':
            return self._packDEB(verbose)
            

class AutoToolsWrapper(PackageWrapper):
    """ Wrapper around GNU Autotools system. """
    
    def __init__(self):
        """ Setups the tool with the packageprofile.
        """
        PackageWrapper.__init__(self)
        
    def addScript(self, script, mode='post'):
        if not mode in ['post','pre','postun','preun']: raise UnsupportedScriptMode, mode
        scriptfile = self.srcdir / script
        if not scriptfile.exists(): raise FileDoesNotExistError, scriptfile
        key = '%sscript' % mode
        self.scripts[key] = stripShebang(scriptfile)
        
    def verify(self):
        """ Verify package is supported. """
        if not hasattr(self,'filename'): raise PackageAttributeNotDefined, 'filename'
        if not hasattr(self,'installroot'): raise PackageAttributeNotDefined, 'installroot'
        if not self.installroot: raise PackageAttributeNotDefined, 'installroot'
        filename = self.srcdir / self.filename
        if not filename.exists(): raise FileDoesNotExistError, filename
        if not tarfile.is_tarfile(filename): return False
        return True
        
    def configure(self, **kwargs):
        """ Configuration stage for this class. """
        filename = self.srcdir / self.filename
        if not self.buildsrc.exists():
            unpackTarfile(filename,self.tmpdir)
        
        configure_args = []
        for k,v in kwargs.items():
            configure_args.append('%s=%s' % (k,v))

        if self.verbose:
            cmd = ' '.join(['./configure'] + configure_args)
        else:
            cmd = ' '.join(['./configure'] + configure_args + ['> /dev/null 2>&1'])

        configP = subprocess.Popen(cmd,shell=True,cwd=self.buildsrc)
        configP.wait()
        
        
    def build(self, **kwargs):
        """ Build stage for this class. """
        
        make_args = []
        for k,v in kwargs.items():
            make_args.append('%s=%s' % (k,v))
    
        if self.verbose:
            cmd = ' '.join(['make'] + make_args)
        else:
            cmd = ' '.join(['make'] + make_args + ['> /dev/null 2>&1'])
        
        makeP = subprocess.Popen(cmd,shell=True,cwd=self.buildsrc)
        makeP.wait()        
       
    def install(self, **kwargs):
        """ Installation stage for this class. """

        makeinstall_args = []
        for k,v in kwargs.items():
            makeinstall_args.append('%s=%s' % (k,v))
        
        if self.verbose:
            cmd = ' '.join(['make'] + makeinstall_args + ['install'])
        else:
            cmd = ' '.join(['make'] + makeinstall_args + ['install > /dev/null 2>&1'])

        makeinstallP = subprocess.Popen(cmd,shell=True,cwd=self.buildsrc)
        makeinstallP.wait()        

        
    def _packRPM(self, verbose=False):
        """ RPM handling stage for this class. """
        self.namespace = prepareNS(self)

        buildroot = 'packages/BUILD/%s-%s-%s' % (self.namespace['pkgname'],
            self.namespace['pkgversion'],
            self.namespace['pkgrelease'])
            
        destroot = self.builddir / buildroot
        if destroot.exists(): destroot.rmtree()
        destroot.makedirs()
        self.install(prefix=destroot)
        tmpl = getPackageSpecTmpl(self.templatesdir)
        _specfile = '.'.join([self.namespace['pkgname'],'spec'])
        specfile = self.builddir / _specfile
        
        rpmbuilder = RPMBuilder(ns=self.namespace,template=tmpl,sourcefile=specfile,verbose=verbose)
        return rpmbuilder.build()


class SRPMWrapper(PackageWrapper):
    """ Wrapper around SRPM build system. """

    def __init__(self):
        PackageWrapper.__init__(self)
        
    def verify(self):
        if not hasattr(self,'filename'): raise PackageAttributeNotDefined, 'filename'
        filename = self.srcdir / self.filename
        if not filename.exists(): raise FileDoesNotExistError, filename
        if not filename.endswith('.src.rpm') or not filename.endswith('.srpm'):
            return False
        return True

    def _packRPM(self, verbose=False):
        """ RPM handling stage for this class. """
        self.namespace = prepareNS(self)
        buildroot = 'packages/BUILD/%s-%s-%s' % (self.namespace['pkgname'],
            self.namespace['pkgversion'],
            self.namespace['pkgrelease'])

        destroot = self.builddir / buildroot
        if destroot.exists(): destroot.rmtree()
        destroot.makedirs()
        self.install(prefix=destroot)
        tmpl = getPackageSpecTmpl(self.templatesdir)
        srpmfile = self.srcdir / self.filename

        rpmbuilder = RPMBuilder(ns=self.namespace,template=tmpl,sourcefile=srpmfile,verbose=verbose)
        return rpmbuilder.build()



class BinaryPackageWrapper(PackageWrapper):
    """ Wrapper around binary distribution packages. """
    
    def __init__(self):
        PackageWrapper.__init__(self)
        
    def addScript(self, script, mode='post'):
        if not mode in ['post','pre','postun','preun']: raise UnsupportedScriptMode, mode
        scriptfile = self.srcdir / script
        if not scriptfile.exists(): raise FileDoesNotExistError, scriptfile
        key = '%sscript' % mode
        self.scripts[key] = stripShebang(scriptfile)
        
    def verify(self):
        """ Verify package is supported. """
        if not hasattr(self,'filename'): raise PackageAttributeNotDefined, 'filename'
        if not hasattr(self,'installroot'): raise PackageAttributeNotDefined, 'installroot'
        if not self.installroot: raise PackageAttributeNotDefined, 'installroot'
        filename = self.srcdir / self.filename
        if not filename.exists(): raise FileDoesNotExistError, filename
        if not tarfile.is_tarfile(filename): return False
        return True

    def configure(self, **kwargs):
        """ Configuration stage for this class. """
        filename = self.srcdir / self.filename
        # unpack the tarfile
        if not self.buildsrc.exists():
            unpackTarfile(filename,self.tmpdir)

    def install(self, prefix):
        """ Installation stage for this class. """
        destroot = path(prefix).abspath()
        cpio_copytree(self.buildsrc,destroot)

    def _packRPM(self, verbose=False):
        """ RPM handling stage for this class. """
        self.namespace = prepareNS(self)
        buildroot = 'packages/BUILD/%s-%s-%s' % (self.namespace['pkgname'],
            self.namespace['pkgversion'],
            self.namespace['pkgrelease'])
            
        destroot = self.builddir / buildroot
        if destroot.exists(): destroot.rmtree()
        destroot.makedirs()
        self.install(destroot)
        tmpl = getPackageSpecTmpl(self.templatesdir)
        _specfile = '.'.join([self.namespace['pkgname'],'spec'])
        specfile = self.builddir / _specfile
        
        rpmbuilder = RPMBuilder(ns=self.namespace,template=tmpl,sourcefile=specfile,verbose=verbose)
        return rpmbuilder.build()
        
        
class RPMWrapper(PackageWrapper):
    """ Wrapper around RPM packages. """
    
    def __init__(self):
        PackageWrapper.__init__(self)
        
    def verify(self):
        if not hasattr(self,'filename'): raise PackageAttributeNotDefined, 'filename'
        if not path(self.srcdir / self.filename).exists() or not path(self.pkgdir / self.filename).exists():
            return False
        return True

    def deploy(self, pkgname='rpm', verbose=False):
        """ Since we don't need rpm packaging, we just handle this specifically.
        """
        return 0


class DistroPackageWrapper(PackageWrapper):
    """ Wrapper around packages that already exists for that distro.
    """
    
    def __init__(self):
        PackageWrapper.__init__(self)
        
    def verify(self):
        # FIXME : this is fake. we should actually check the distro repository to see if this package
        # actually exists.
        return True
        
    def deploy(self, pkgname='rpm', verbose=False):
        return 0



class RPMBuilder:

    ns = {}
    template = ''
    sourcefile = ''
    verbose = False

    def __init__(self, ns, template, sourcefile, verbose=False):
        self.ns = ns
        self.template = template
        self.sourcefile = sourcefile
        self.verbose = verbose

    def _write(self):
        f = path(self.sourcefile)
        out = open(f, 'w')
        t = Template(file=str(self.template), searchList=[self.ns])  
        out.write(str(t))
        out.close()

    def build(self):

        if self.sourcefile.endswith('.spec'):
            # spec file
            self._write()
            if self.verbose:
                cmd = 'rpmbuild -bb %s' % (self.sourcefile)
            else:
                cmd = 'rpmbuild -bb %s > /dev/null 2>&1' % (self.sourcefile)

        if self.sourcefile.endswith('.src.rpm') or self.sourcefile.endswith('.srpm'):
            # srpm file
            if self.verbose:
                cmd = 'rpmbuild --rebuild %s' % (self.sourcefile)
            else:
                cmd = 'rpmbuild --rebuild %s > /dev/null 2>&1' % (self.sourcefile)

        rpmP = subprocess.Popen(cmd,shell=True)
        rpmP.wait()
        
        return rpmP.returncode        


