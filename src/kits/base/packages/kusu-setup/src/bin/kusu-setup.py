#!/usr/bin/env python
import os
import sys
import time
import signal
from path import path
import subprocess

KUSU_SERVER_PATH = '/opt/kusu/sbin/kusu-server'

def error(msg):
    print msg
    sys.exit(1)

def run(conf, deps='/opt/kusu/setup/dependencies', textmode=False):
    cf = path(conf)
    if not cf.isfile():
        error('Config file not found.')

    # Detect OS,ver,arch
    
    # Check for dependencies
    deps = path(deps)
    if not deps.isfile():
        error('Dependencies list not found.')
    setupMinimalDeps(deps)

    # Start Kusu Server
#    kusu_server_pid = startKusuServer()

    # Start config environment
    if isXRunning() and not textmode:
        startGraphicalInstall()
        return

    # Handover to Kusu Server
    startInstall(conf)

    # kill Kusu Server
#    os.kill(kusu_server_pid, signal.SIGTERM)

def setupMinimalDeps(deps):
    pass


def startKusuServer():
    pid = os.fork()
    if pid != 0:
        waitForServer()
        return pid
    kusuServerProcess()


def waitForServer():
    globals()['server_ready'] = False
    def serverReady(signum, frame):
        globals()['server_ready'] = True
    signal.signal(signal.SIGUSR1, serverReady)
    while not server_ready:
        time.sleep(3)
    globals().pop('server_ready')


def kusuServerProcess():
    import traceback, Ice
    from springpython.context import ApplicationContext
    from springpython.config import XMLConfig
    from kusu.server import KusuServerApplicationContext

    app_ctx_cfg = '/opt/kusu/server/conf/applicationContext.xml'
    try:
        ctx = ApplicationContext([KusuServerApplicationContext(),
                                  XMLConfig(app_ctx_cfg)])
        proxy = ctx.get_object('kusuServerAdapterProxy')
        iceObj = proxy.iceObj
        ppid = os.getppid()
        os.kill(ppid, signal.SIGUSR1)
        iceObj.waitForShutdown()
    except:
        traceback.print_exc()
        sys.exit(1)
    sys.exit(0)


def isXRunning():
    return False


def startGraphicalInstall():
    return


def startInstall(conf):
    import Ice
    Ice.loadSlice('/opt/kusu/server/conf/kusu.ice')
    import kusu
    import kusu2
    ic = Ice.initialize(['--Ice.Config=/opt/kusu/server/conf/ice.conf'])
    base = ic.stringToProxy('InstallServant:ssl -p 10000')
    install = kusu.remote.ISetupPrx.checkedCast(base)
   
    try:
        s = ''
        if path(conf).exists():
            s = open(conf).read()
        install.install(s)
        print 'Success'
    except kusu.remote.InstallException, e:
        print 'Install Exception(s):'
        for m in e.messages:
            print '%s: %s' % (m.title, m.msg)



#    base = ic.stringToProxy('NetworkServant:ssl -p 10000')
#    network = kusu2.config.net.INetworkPrx.checkedCast(base)
#    intf = network.getInterfaces()
#    print network.getInterfaceConfig(intf[0])
    return

if __name__ == '__main__':
    run(sys.argv[1], textmode=True)
