#!/usr/bin/python2.4

import sys, os
sys.path.append(os.path.abspath('../src/') )

import traceback, Ice
from springpython.context import ApplicationContext
from springpython.config import XMLConfig
from kusu.server import KusuServerApplicationContext


if __name__ == "__main__" :
            
    status = 0
    iceObj=None
    try:
        
        ctx = ApplicationContext([KusuServerApplicationContext(),
                                  XMLConfig("/opt/kusu/server/conf/applicationContext.xml")])
        proxy = ctx.get_object("kusuServerAdapterProxy")
        iceObj = proxy.iceObj
        iceObj.waitForShutdown()
    except:
        traceback.print_exc()
        status = 1
    
    if iceObj:
        #Clean up 
        try:
            iceObj.destroy()
        except:
            traceback.print_exc()
            status = 1
    
    sys.exit(status)
