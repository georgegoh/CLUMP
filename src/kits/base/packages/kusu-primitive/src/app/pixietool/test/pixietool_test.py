#!/usr/bin/env python

import os
import tempfile
import logging
from primitive.core.command import CommandFailException
from primitive.pixietool.commands import GeneratePXEConfCommand
try:
    import subprocess
except:
    from popen5 import subprocess
#from primitive.modules.core import command
import errno 
from nose.tools import assert_raises

#initialise to some failsafes
tmpBaseDir = '/tmp/non_existent'
pxedir =  '/tmp/non_existent'
kernel_path =  '/tmp/non_existent'
initrd_path =  '/tmp/non_existent'
tmpTftpDir = '/tmp/non_existent'

def __touch(filename):
    f = open(filename,'w')
    f.close()

def setup():
    global pxedir
    global kernel_path
    global initrd_path
    global tmpBaseDir
    global tmpTftpDir
    tmpBaseDir = tempfile.mkdtemp('primitive')
    tmpTftpDir = tempfile.mkdtemp('primitive')
    pxedir = ''.join([tmpTftpDir,'/pxelinux.cfg'])
    kernel_path = ''.join([tmpBaseDir,'/kernel'])
    initrd_path =  ''.join([tmpBaseDir,'/initrd'])

    __touch(kernel_path)
    __touch(initrd_path)
    os.makedirs(pxedir)
    test_pxeconf = """# PXE File for ${ident}
#if $varExists('preamble')
$preamble
#end if
default localdisk
prompt 0
label localdisk
      localboot $localboot
label Reinstall
      kernel $kernelName
      append initrd=$initrdName #slurp
#if  $varExists('instIP')
instIP = $instIP #slurp
#end if
$params
"""
    fn = open(tmpBaseDir+"/pxe.tmpl",'w')
    fn.write(test_pxeconf)
    fn.close()
    

def teardown():
    os.remove(initrd_path)
    os.remove(kernel_path)
    os.remove(''.join([tmpBaseDir,"/pxe.tmpl"]))
    os.removedirs(tmpBaseDir)


class TestPixieTool(object):
    ''' Test PXE Tool'''
    def setUp(self):
        pass
    def tearDown(self):
        pass
        
    def testGeneratePXEConfCommand(self):
        ''' Test generation of PXE Configuration.'''
        
        print tmpTftpDir
        print kernel_path
        print initrd_path
        print pxedir
        expected_out ="""# PXE File for fe80-20c-29ff-fe40-33f
#Comment
default localdisk
prompt 0
label localdisk
      localboot 0
label Reinstall
      kernel kernel
      append initrd=initrd instIP = 192.168.1.1 ks="file://ks.cfg"
"""
        t = GeneratePXEConfCommand(identifierList = ['fe80-20c-29ff-fe40-33f'],
                                   preamble ='#Comment',
                                   name = 'GeneratePXEConf',
                                   tftpdir = tmpTftpDir,
                                   instIP = '192.168.1.1',
                                   kname = 'kernel',
                                   kpath =  kernel_path,
                                   iname = 'initrd',
                                   ipath = initrd_path,
                                   params = 'ks="file://ks.cfg"',
                                   localboot = 0,
                                   template  = tmpBaseDir + '/pxe.tmpl',
                                   logged = False)
                                    
        t.execute()
        # Validate File
        assert os.path.exists(''.join([tmpTftpDir,'/kernel']))
        assert os.path.exists (''.join([tmpTftpDir,'/initrd']))
        assert os.path.exists (''.join([pxedir,'/fe80-20c-29ff-fe40-33f']))
        
        pxefile = open(''.join([pxedir,'/fe80-20c-29ff-fe40-33f']),'r')
        print expected_out
        out =  pxefile.read()
        print out
        assert out == expected_out
        pxefile.close()
        os.remove(''.join([tmpTftpDir,'/kernel']))
        os.remove(''.join([tmpTftpDir,'/initrd']))
        os.remove(''.join([pxedir,'/fe80-20c-29ff-fe40-33f']))
        os.removedirs(pxedir)


    def testGenerateELILOConfCommand(self):
        ''' Test generation of ELILO Configuration '''
        input_dict =  { 'identifierList' :  ['fe80-20c-29ff-fe40-33f'],
                        'name' : 'GeneratePXEConf',
                        'backend' : 'ELILO',
                        'tftpdir' : tmpTftpDir,
                        'instIP' : '192.168.1.1',
                        'kname' : 'kernel',
                        'kpath' :  kernel_path,
                        'iname' : 'initrd',
                        'ipath' : initrd_path,
                        'params' : 'ks="file://ks.cfg" " ',
                        'localboot' : 0,
                        'template' : tmpBaseDir + '/pxe.tmpl',
                        'logged' : False }
        assert_raises(NotImplementedError,GeneratePXEConfCommand,**input_dict)
