#!/usr/bin/env python
#
# $Id$
#

from kusu.util.errors import *
from kusu.core.app import KusuApp
from kusu.core import database as db
from kusu.hardware import probe
import kusu.util.log as kusulog

from path import path
import os
import sys
import re
import base64
import xmlrpclib
from optparse import SUPPRESS_HELP, OptionParser

try:
    import subprocess
except:
    from popen5 import subprocess

FILTERED_KITS = ['base', 
                 'centos', 'rhel', 
                 'lava', 'lsf', 
                 'hpc', 'ofed', 'platform_ofed', 'OCS-GUI',
                 'ntop', 'ganglia', 'cacti']

class Server:
    def __init__(self, url='http://www.hpccommunity.org/xmlrpc.php'):
        self.server = xmlrpclib.Server(url)

    def register(self, data):
        return self.server.kusu.register(data)

    def getKits(self):
        try:
            return self.server.kusu.getKits()
        except:
            return []

class App(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)

        usage = 'kusu_register: A tool to register your cluster with Project Kusu.'
        self.parser = OptionParser(usage)

        self.parser.add_option('-v', '--verbose', dest='verbose', action="store_true", help=self._('Turn on verbose output'))
        self.parser.add_option('', '--version', dest='version', action="store_true", help=self._('Display version of tool'))
        self.parser.add_option('--dbdriver', dest='dbdriver',
                               help=self._('Database driver (sqlite, mysql, postgres)'))
        self.parser.add_option('--dbdatabase', dest='dbdatabase',
                               help=self._('Database'))
        self.parser.add_option('--dbuser', dest='dbuser',
                               help=self._('Database username'))
        self.parser.add_option('--dbpassword', dest='dbpassword',
                               help=self._('Database password'))

        self.svr = Server()

    def parseArgs(self):
        (options, args) = self.parser.parse_args()

        #self.checkArgs(options)
 
        dbdriver = os.getenv('KUSU_DB_ENGINE')
        if not dbdriver or dbdriver not in ['mysql','postgres']:
            dbdriver = 'postgres' # default to postgres
            #dbdriver = 'mysql' # default to mysql

        dbdatabase = 'kusudb'
        dbuser = 'apache'
        dbpassword = None

        if options.dbdriver:
            dbdriver = options.dbdriver
        if options.dbdatabase:
            dbdatabase = options.dbdatabase
        if options.dbuser:
            dbuser = options.dbuser
        if options.dbpassword:
            dbpassword = options.dbpassword

        try:
            self.dbs = db.DB(dbdriver, dbdatabase, dbuser, dbpassword)
        except (UnsupportedDriverError, NoSuchDBError):
            sys.exit(1)

        if options.version:
            self.getVersion()
            sys.exit(0)

        self.verbose = False
        if options.verbose: self.verbose = True

        self.submit()
            

    def getVersion(self):
        self.stdoutMessage('kusu_register 1.1\n')
 
    def getKits(self):
        kits = self.dbs.Kits.select()

        klist = []
        filter_kits = [ k.lower() for k in  FILTERED_KITS + self.svr.getKits()]

        for kit in kits:
            if kit.rname.lower() in filter_kits:
                klist.append('%s-%s-%s' % (kit.rname, kit.version, kit.arch))
        return klist

    def getDistro(self):

        dist = os.getenv('KUSU_DIST', '')
        dist_arch = os.getenv('KUSU_DIST_ARCH', '')
        distver = os.getenv('KUSU_DISTVER', '')

        return '%s-%s-%s' % (dist, distver, dist_arch)

    def getDMI(self):

        dmiTypes = {'DMI type 9' : ('System Slot', 'SYSTEM'),
                    'DMI type 8' : ('Port', 'SYSTEM'),
                    'DMI type 16': ('Memory Array', 'MEM'),
                    'DMI type 7' : ('Cache', 'SYSTEM'),
                    'DMI type 38': ('IPMI', 'SYSTEM'),
                    'DMI type 3' : ('Chassis','SYSTEM'),
                    'DMI type 1' : ('System','SYSTEM'),
                    'DMI type 0' : ('Bios', 'SYSTEM'),
                    'DMI type 10': ('Devices','SYSTEM'),
                    'DMI type 2' : ('Mainboard', 'SYSTEM'),
                    'DMI type 4' : ('Processor', 'CPU'),
                    'DMI type 17': ('Memory Slot', 'MEM')
                    }

        dmiDict = {}
        for i in dmiTypes.keys():
            dmiDict[i] = []

        p = subprocess.Popen('dmidecode',
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        y, err = p.communicate()
        retcode = p.returncode

        data = y.split('Handle 0x')
        data.pop(0)
        for i in data:
            i = i.replace('\t','')
            i = i.strip()
            li = i.split('\n')
    
            newli = li[1:]
            key = newli.pop(0).split(',')[0]
            if key in dmiTypes.keys():
                dmiDict[key].extend(newli)
            else:
                key = li[0].split(',')[1].strip()
                if key in dmiTypes.keys():
                    dmiDict[key].extend(li[1:])

        mem_size = 0
        dmiInfo = {}

        for k,v in dmiDict.iteritems():
            for i in v:
                key = dmiTypes[k][0]
                if key.startswith('Memory Slot'):
                    if i.startswith('Size:'):
                        size = i.split(':')[1].strip().split(' ')[0]
                        try:
                            size = int(size)
                            mem_size = mem_size + size                            
                            dmiInfo['memory'] = mem_size
                        except: pass

                elif key == 'System':
                    s = i.split(':')
                    try: key = s[0]
                    except: key = ''
                    
                    try: txt = s[1].strip()
                    except: txt = ''
                    
                    if key in ['Manufacturer', 'Product Name', 'Version', 'Serial Number']:
                        if not dmiInfo.has_key('system'): dmiInfo['system']= {}
                        dmiInfo['system'][key.lower()] = txt

                elif key == 'Mainboard':
                    s = i.split(':')
                    try: key = s[0]
                    except: key = ''
                    
                    try: txt = s[1].strip()
                    except: txt = ''
                    
                    if key in ['Manufacturer', 'Product Name', 'Version', 'Serial Number']:
                        if not dmiInfo.has_key('mainboard'): dmiInfo['mainboard']= {}
                        dmiInfo['mainboard'][key.lower()] = txt
            
        return dmiInfo

    def getNetwork(self):
        net =  probe.getPhysicalInterfaces()

        for k,v in net.iteritems():
            if not v['device']: v['device'] = ''
            if not v['vendor']: v['vendor'] = ''
           
            net[k] = v
        return net

    def getInterconnect(self):
        pass

    def getCPU(self):

        f = open('/proc/cpuinfo', 'r')
        cpu = f.readlines()
        f.close()

        proc_count = 0
        cpuDict= {}
        for i in cpu:
            try: txt = i.split(':')[1].strip()
            except: txt = ''

            if i.startswith('processor'):
                proc_count = txt
                cpuDict[txt] = {}
            elif i.startswith('vendor_id'):
                cpuDict[proc_count]['vendor'] = txt
            elif i.startswith('model name'):
                cpuDict[proc_count]['model'] = txt
            elif i.startswith('cpu MHz'):
                cpuDict[proc_count]['mhz'] = txt
            elif i.startswith('cpu family'):
                cpuDict[proc_count]['family'] = txt
            elif i.startswith('model'):
                cpuDict[proc_count]['cpu model'] = txt
            elif i.startswith('stepping'):
                cpuDict[proc_count]['cpu stepping'] = txt
            
        return cpuDict

    def getKusuRelease(self):
        release = path('/etc/kusu-release')
        ver = ''
        build = ''

        if release.exists():
            try:
                f = open(release, 'r')
                s = f.read()
                f.close()

                ver = re.compile('[0-9]+\.[0-9]+\.?[0-9]*').findall(s)[0]
                build = re.compile('[0-9]+').findall(s)[-1]
            except: pass

        return {'verison': ver, 'build': build}

    def prompt(self):
        msg = """Project Kusu respect your privacy. By registering your cluster...

Do you wish to continue (y/n)?
"""
        print msg, 
        res = ''
        while not (res.lower() == 'y' or res.lower() == 'n'):
            res = sys.stdin.readline().strip()
            if res.lower() == 'n':
                sys.exit(0)

    def run(self):
        self.parseArgs()

    def getSysInfo(self):
        d = {}

        if self.verbose:
            print "Gathering kits information..."
        d['kits'] = self.getKits()
        
        if self.verbose:
            print "Gathering distro information..."
        d['os'] = self.getDistro()

        if self.verbose:
            print "Gathering Kusu version..."
        d['kusu version'] = {}
        d['kusu version'].update(self.getKusuRelease())

        if self.verbose:
            print "Gathering system information..."

        d['sysinfo'] = {}
        try:
            dmi = self.getDMI()
            d['sysinfo'].update(dmi)
        except: pass

        try:
            d['sysinfo']['network'] = {}
            d['sysinfo']['network'].update(self.getNetwork())
        except: pass

        try:
            d['sysinfo']['cpu'] = {}
            d['sysinfo']['cpu'].update(self.getCPU())
        except: pass

        return d

    def submit(self):

        self.prompt()
        
        try:
            errStr = ''
            clusterid = self.svr.register(self.getSysInfo()) 
            print
            print "Thank you for registering with Project Kusu."
            print "You are cluster #%s." % clusterid

        except xmlrpclib.Fault, err:
            errStr = err.faultString
        except xmlrpclib.ProtocolError, err:
            errStr = err.errmsg
        except Exception, e:
            errStr = str(e)
 
        if errStr:
            sys.stderr.write('Unable to register your system. Reason: %s\n' % errStr)
            sys.stderr.write('Please try again later.\n')
            sys.exit(1)

if __name__ == '__main__':
    if os.getuid() != 0:
        sys.stderr.write('You need to be root to run kusu_register.\n')
        sys.exit(1)

    app = App()
    app.run()
    
