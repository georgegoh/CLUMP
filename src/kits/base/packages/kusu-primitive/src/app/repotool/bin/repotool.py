#!/usr/bin/env python

import os
import sys
import tempfile
import logging
from primitive.core.command import CommandFailException
from primitive.repotool.commands import CreateRepoCommand
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
    parser.add_option("--os",action="store",dest="os")
    parser.add_option("--version",action="store",dest="version")
    parser.add_option("--arch",action="store",dest="arch")
    parser.add_option("--kitPath",action="store",dest="kitPath")
    parser.add_option("--repoType",action="store",dest="repoType")
    parser.add_option("--repoPath",action="store",dest="repoPath")
    parser.add_option("--updateImg",action="store",dest="updateImg")
    parser.add_option("--logged",action="store_true",dest="logged", 
                      default=False)
    parser.add_option("--locked",action="store_true",dest="locked", 
                      default=False)
        

    (option,args) = parser.parse_args(sys.argv[1:])

    input_dict = {}
    # check mandatory args.
    if (not option.os) or\
            (not option.version) or\
            (not option.arch) or\
            (not option.kitPath) or\
            (not option.repoType) or\
            (not option.repoPath):
        print 'Required argument not supplied!'
        sys.exit(-1)
        
            
    input_dict['name']  = 'CreateRepo'
    input_dict['repoName'] = 'TestRepo'
    
    input_dict['os'] = option.os
    input_dict['version'] = option.version
    input_dict['arch'] = option.arch
    input_dict['kitPath'] = option.kitPath
    input_dict['repoType'] = option.repoType
    input_dict['repoPath'] = option.repoPath
    if not option.logged:
        input_dict['logged'] = False
    if option.locked:
        input_dict['locked'] = True
    if option.updateImg:
        input_dict['updates'] = option.updateImg
    t = CreateRepoCommand(**input_dict)
    t.execute()
    
                      
                    
                     
