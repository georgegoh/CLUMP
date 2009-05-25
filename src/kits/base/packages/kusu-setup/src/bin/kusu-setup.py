#!/usr/bin/env python
import os
import sys
import time
import signal
import subprocess
# ICE 
import Ice
Ice.loadSlice('/opt/kusu/server/conf/kusu.ice')
import kusu
import kusu2

KUSU_SERVER_PATH = '/opt/kusu/sbin/kusu-server'

def error(msg):
    print msg
    sys.exit(1)

def run(conf, deps='/opt/kusu/setup/dependencies', textmode=False):
    if not os.path.isfile(conf):
        error('Config file not found.')

    # Detect OS,ver,arch
    
    # Check for dependencies
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
    """ deps is a string location of the text file containing the list
        of dependencies to be downloaded remotely and installed.
    """
    if not os.path.isfile(deps):
        error('Dependencies list not found.')

    f = open(deps)
    # remove newline characters for each line.
    lines = [l.strip() for l in f]
    # remove empty lines.
    lines = [l for l in lines if l]
    # get list of missing dependencies.
    missing_deps = [pkg for pkg in lines if not isPkgInstalled(pkg)]
    if missing_deps:
        error('Required dependencies missing: %s' % missing_deps)


def isPkgInstalled(pkgname):
    """ Check using the 'rpm -q' command whether a package is installed.
        If the return value starts with the package name, then returns True.
        Returns False otherwise.
    """
    rpm_check = subprocess.Popen(['/bin/rpm', '-q', pkgname],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
    out,err = rpm_check.communicate()
    if out.startswith(pkgname):
        return True
    return False


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
    ic = Ice.initialize(['--Ice.Config=/opt/kusu/server/conf/ice.conf'])
    base = ic.stringToProxy('InstallServant:ssl -p 10000')
    install = kusu.remote.ISetupPrx.checkedCast(base)
   
    try:
        s = ''
        if os.path.isfile(conf):
            s = open(conf).read()
        install.verify(s)
        install.install(s)
        print 'Kusu successfully installed.'
    except kusu.remote.InstallException, e:
        print 'Install Config Exception(s):'
        for i,m in enumerate(e.messages):
            print '%s. %s: %s' % (i+1, m.title, m.msg)

    return

if __name__ == '__main__':
    run(sys.argv[1], textmode=True)
