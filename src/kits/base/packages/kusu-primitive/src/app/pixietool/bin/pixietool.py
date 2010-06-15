#!/usr/bin/env python

import os
import sys
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
from optparse import OptionParser

class AppException(Exception):
    pass
if __name__ == '__main__':
    parser = OptionParser()
    #command related params
    parser.add_option("--identifier",action="store",dest="identifier")
    parser.add_option("--logged",action="store_true",dest="logged", 
                      default=False)
    parser.add_option("--locked",action="store_true", dest = "locked",
                      default=False)
    parser.add_option("--lockdir",action="store",dest="lockdir")
    parser.add_option("--logdir",action="store",dest="logdir")
    #output reladed params
    parser.add_option("--tftpdir",action="store",dest="tftpdir")
    parser.add_option("--instip",action="store",dest="instip")
    parser.add_option("--kernel",action="store",dest="kernel")
    parser.add_option("--kpath",action="store",dest="kpath")
    parser.add_option("--initrd",action="store",dest="initrd")
    parser.add_option("--ipath",action="store",dest="ipath")
    # config file related params
    parser.add_option("--params",action="store",dest="params")

    parser.add_option("--preamble",action="store",dest="preamble")

    parser.add_option("--localboot",action="store",type="int",
                      dest="localboot",default=0)
    parser.add_option("--template",action="store",dest="template")
    (option,args) = parser.parse_args(sys.argv[1:])

    input_dict = {}
    input_dict['name']  = 'GeneratePixieConf'
    # check mandatory args.
    if (not option.identifier) or\
            (not option.tftpdir) or\
            (not option.kernel) or\
            (not option.kpath) or\
            (not option.initrd) or\
            (not option.ipath) or\
            (not option.params) or\
            (not option.template):
        print 'Required argument not supplied!'
        sys.exit(-1)
            
    if option.preamble:
        input_dict['preamble'] = option.preamble
    if option.lockdir:
        input_dict['lockdir'] = option.lockdir
    if option.logdir:
        input_dict['logdir'] = option.logdir
    if option.instip:
        input_dict['instIP'] =  option.instip


    input_dict['identifierList'] = [option.identifier]
    input_dict['tftpdir'] = option.tftpdir
    input_dict['kname'] = option.kernel
    input_dict['kpath'] = option.kpath
    input_dict['iname'] = option.initrd
    input_dict['ipath'] = option.ipath
    input_dict['params'] = option.params
    input_dict['template'] = option.template
    input_dict['localboot'] = option.localboot
    if not option.logged:
        input_dict['logged'] = False
    if option.locked:
        input_dict['locked'] = True

#     identifierList = ['fe80-20c-29ff-fe40-33f'],
#     preamble ='#Comment',
#     name = 'GeneratePixieConf',
#     tftpdir = ,
#     instIP = '192.168.1.1',
#     kname = 'kernel',
#     kpath =  kernel_path,
#     iname = 'initrd',
#     ipath = initrd_path,
#     params = 'ks="file://ks.cfg"',
#     localboot = 0,
#     template  = tmpBaseDir + '/pxe.tmpl',
#     logged = False)


    t = GeneratePXEConfCommand(**input_dict)
    t.execute()
    
                      
                    
                     
