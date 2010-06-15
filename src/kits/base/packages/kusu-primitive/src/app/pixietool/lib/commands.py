#!/usr/bin/env python
import os
import sys
import shutil
import atexit
from primitive.core.command import Command
from primitive.core.command import CommandFailException
from path import path

import Cheetah.Template



class PixieCommand(Command):
    def __init__(self,**kwargs):
        Command.__init__(self,**kwargs)
        self.SUPPORTED_BACKENDS = {'PXELINUX':'/pxelinux.cfg/'\
                                       ,'ELILO': '/elilo.conf/' }
        # provided by backend?
        #optional directory
        self.dir = '/tftpboot'
        self.backend = self.SUPPORTED_BACKENDS.keys()[0]
        if 'tftpdir' in kwargs:
            self.dir = kwargs['tftpdir']
        if not self.dir.endswith('/'):
            ''.join([self.dir,'/'])
        if 'backend' in kwargs:
            self.backend = kwargs['backend']

        if self.backend not in self.SUPPORTED_BACKENDS.keys():
            raise CommandFailException,\
                'The backend %s is not supported'% self.backend
        if self.backend == 'ELILO':
            raise NotImplementedError,'Backend Support for Elilo not Implemented'
        
        

        
class ReturnInfoCommand(PixieCommand):
    def __init__(self,**kwargs):
        PixieCommand.__init__(self,kwargs)
        try:
            self.ilist = kwargs['identifierList']
        except KeyError:
            raise CommandFailException,\
                'This command requires a list of identifiers!'
        self.ilist = kwargs['identifierList']
        if 'all' in kwargs.keys() and kwargs['all']:
            self.allIdentifiers = True
        else:
            self.allIdentifiers = False

    def execImpl(self):
        if self.backend == 'PXELINUX':
            lookupdir= ''.join([self.dir, '/pxelinux.cfg'])
        if not os.path.isdir(lookupdir):
            raise CommandFailException,'The tftpboot directory is in an inconsistent state'
        # the identifier can be different from the filename , as with
        # Elilo, return a tuple of name/path
        if self.allIdentifiers:
            filtered_list = os.listdir(lookupdir)
        else:
            filtered_list =\
                [ x for x in os.listdir(lookupdir) if x in self.ilist]
        # identifer / location pair
        ilist = map( lambda x : (x,os.path.join(self.dir,x)) , filtered_list)
        
        # available kernels
        kernel_list = [ x for x in os.listdir(self.dir) \
                            if os.path.isfile (os.path.join(self.dir,x))\
                            and x.startswith("kernel")]
        initrd_list = [ x for x in os.listdir(self.dir) \
                            if os.path.isfile(os.path.join(self.dir,x))\
                            and x.startswith("initrd")]
        # available initrds
        # ideally we can break this into 2 functions , single and all
        # single returns the kernel/initrd associated by reading the conf file
        # all returns all kernels/initrds
        return (kernel_list,initrd_list, ilist)

    
class GeneratePXEConfCommand(PixieCommand):
    def __init__ (self,** kwargs):
        PixieCommand.__init__(self,**kwargs)
        #mandatory args
        try:
            self.template = kwargs['template']
            self.identifierList = kwargs['identifierList']
            self.kernelName = kwargs['kname']
            self.kernelPath = kwargs['kpath']
            self.initrdName = kwargs['iname']
            self.initrdPath = kwargs['ipath']
            self.params = kwargs['params']
        except KeyError:
            raise CommandFailException,'required key not supplied'
        #optional args
        self.localboot = 0
        self.noUpdate = False
        if 'localboot' in kwargs:
            self.localboot = kwargs['localboot']
        if 'noUpdate' in kwargs:
            self.noUpdate = kwargs['noUpdate']
        if 'preamble' in kwargs:
            self.preamble = kwargs['preamble']
        if 'syslogIP' in kwargs:
            self.syslogIP = kwargs['syslogIP']
        if 'instIP' in kwargs:
            self.instIP = kwargs['instIP']
        self.kwargs = kwargs


    def execImpl(self):
        # TODO- check for duplicates in identifer list
        backend_dir = self.SUPPORTED_BACKENDS[self.backend]
        configMap = {}
        for i in self.identifierList:
            configMap[i] = self.__genConfig(i)
        if not self.noUpdate:
            try:
                shutil.copy2(self.kernelPath, self.dir)
            except Exception,e:
                raise CommandFailException,'Failed to copy kernel %s to %s' %\
                    ( self.kernelPath, self.dir)
            try:
                shutil.copy2(self.initrdPath, self.dir)
            except Exception,e:
                raise CommandFailException,'Failed to copy initrd'
        # write each config under the filename

        fnames = []
        for k,v in configMap.items():
            fname = '/'.join([self.dir, self.SUPPORTED_BACKENDS[self.backend], k])
            self.__writeFile(fname, v)
            fnames.append(fname)

        # keep our command i/o consistent. 
        # we should be returning the full configMap here. and also
        # in the list 
        return (self.kernelName,self.initrdName,configMap, fnames)


    def __genConfig(self,ident):
        if self.backend == 'PXELINUX':
            return self.__genPXELINUXConfig(ident)
        if self.backend == 'ELILO':
            return self.__genELILOConfig(ident)
    
    def __genELILOConfig(self,ident):
        pass


    def __genPXELINUXConfig(self,ident):
        # we will usually call cheetah here.
        # configToolCommand() or ssh the xml
        searchDict = { 'ident' : ident,
                       'localboot' : self.localboot,
                       'kernelName' : self.kernelName,
                       'initrdName' : self.initrdName,
                       'params' : self.params }
        if hasattr(self,'preamble'):
            searchDict['preamble'] = self.preamble
        if hasattr(self,'syslogIP'):
            searchDict['syslogIP'] =  self.syslogIP
        if hasattr(self,'instIP'):
            searchDict['instIP'] =  self.instIP
        if hasattr(self,'kwargs'):
            searchDict['kwargs'] =  self.kwargs
        tmpl = path(self.template)
        if not tmpl.exists() and not tmpl.isfile():
            raise CommandFailException,'Failed opening template file'
        try:
            t = Cheetah.Template.Template(file=str(tmpl),\
                                              searchList = [searchDict])
        except Exception,e:
            raise CommandFailException,'Failed to parse template %s : %s'%\
                (self.template, e)
        
        return str(t)

    # part of support module
    def __writeFile(self, name , buf):
        try:
            fn = open(name,'w')
            try:
                fn.write(buf)
            finally:
                fn.close()
        except IOError:
            raise CommandFailException,'Failed writing config file'


# if __name__ == '__main__':
#     try:
#         foo = ReturnInfoCommand(None,all=True)
#         klist , ilist , flist = foo.execute()
#         print klist
#         print ilist
#         print flist
#     except CommandFailException, e:
#         print e
#     try:
#         identl = ['01-00-0c-29-95-be-96']
#         foo = ReturnInfoCommand(backendName='PXELINUX',identifierList = identl)
#         klist , ilist , flist = foo.execute()
#         print klist
#         print ilist
#         print flist
#     except CommandFailException, e:
#         print e

#     try:
#         bar = \
#             GeneratePXEConfCommand(['de-ad-be-ef'],\
#                                        instIP = '192.168.1.1',\
#                                        kname = 'kernel.test.1',\
#                                        kpath = '/fake/kusu/kernel.test.1',\
#                                        iname = 'initrd.test.img',\
#                                        ipath = '/fake/kusu/initrd.test.img',\
#                                        params = 'ks="file://ks.cfg" " ',\
#                                        localboot = 0)
#         klist,ilist,flist = bar.execute()
#         print klist
#         print ilist
#         print flist
#     except CommandFailException,e:
#         print e

                                     
                                     


